"""H14 -- estimacao, rotulo embaralhado e avaliacao pareada (spec 027).

O QUE ESTE MODULO MEDE

Nao "o modelo e bom?", mas tres perguntas encadeadas, em ordem:

  1. O que ele achou esta nos DADOS ou na capacidade dele?
     -> comparacao contra o MESMO modelo com rotulos embaralhados
  2. Se esta nos dados, o sinal PAGA as barreiras?
     -> razao de chances no subconjunto decidido contra a razao de empate
  3. Se paga, ele supera as regras e se sustenta fora da amostra?

A primeira pergunta e a que torna as outras interpretaveis. Um classificador
sempre encontra alguma estrutura; sem a linha de base embaralhada, capacidade
do modelo seria lida como estrutura dos dados.

O LIMIAR DE DECISAO VEM DAS BARREIRAS, NAO DE ESCOLHA

    p_limiar = sl_mult / (sl_mult + tp_mult) = 1,5 / 4,5 = 0,3333

E a probabilidade de alvo acima da qual a expectativa fica positiva:
`p x tp - (1-p) x sl > 0`. Nao ha nada a ajustar aqui -- o numero cai das
barreiras que o bot ja usa.

Observado ao acaso: 23,4% dos eventos atingem o alvo. Abaixo de 33,33%. O modelo
so opera onde consegue elevar a probabilidade acima desse ponto.

BAIXA CAPACIDADE POR ESCOLHA

Cinco atributos e um intercepto sobre ~16.000 amostras: 2.700 por parametro.
Sobreajuste por capacidade e implausivel por construcao, e o que sobrar de
desempenho e atribuivel aos dados. H13 obteve 1 aprovacao em 96 testes -- abaixo
da expectativa do acaso -- e um modelo flexivel multiplicaria esse problema.
"""
import warnings
from dataclasses import dataclass, field
from typing import Dict, Optional

import numpy as np
import pandas as pd

from backtesting.volatilidade import ganho_de_timing
from config.settings import EDGE_MIN_TRADES
from strategy.barreira_tripla import ParametrosBarreira
from utils.logger import get_logger

log = get_logger("modelo")

# Minimo de amostras de treino apos a purga para a estimacao valer.
MIN_TREINO = 200

# Quanto o modelo precisa superar o embaralhado, em pontos percentuais de ganho
# de timing, para nao ser considerado indistinguivel. Nao e limiar de
# significancia estatistica: e a margem abaixo da qual a diferenca cabe no ruido
# de uma unica permutacao.
MARGEM_VS_EMBARALHADO_PP = 1.0


def limiar_de_decisao(params: Optional[ParametrosBarreira] = None) -> float:
    """Probabilidade de alvo acima da qual a expectativa fica positiva.

        p x tp - (1 - p) x sl > 0   =>   p > sl / (sl + tp)

    Cai das barreiras. Nao e parametro ajustavel.
    """
    p = params or ParametrosBarreira()
    return p.sl_mult / (p.sl_mult + p.tp_mult)


def estimar(X: pd.DataFrame, y: pd.Series):
    """Regressao logistica. Devolve `None` quando a estimacao nao e valida.

    Devolver `None` em vez de propagar excecao e deliberado: falha de
    convergencia, classe unica e colinearidade sao ESTADOS previstos desta
    hipotese (FR-012), nao imprevistos. A colinearidade medida entre candidatos
    descartados chegou a 0,959.
    """
    from statsmodels.discrete.discrete_model import Logit
    from statsmodels.tools.tools import add_constant

    y = pd.Series(y).astype(float)
    if y.nunique() < 2:
        return None
    if len(y) < 2 or X is None or len(X) != len(y):
        return None

    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            modelo = Logit(y.values, add_constant(X.values, has_constant="add"))
            ajuste = modelo.fit(disp=0, maxiter=100)
        if not np.all(np.isfinite(ajuste.params)):
            return None
        if not getattr(ajuste.mle_retvals, "get", lambda *_: True)("converged", True):
            return None
        return ajuste
    except Exception as exc:
        log.warning(f"estimacao falhou: {type(exc).__name__}: {str(exc)[:60]}")
        return None


def prever(ajuste, X: pd.DataFrame) -> Optional[np.ndarray]:
    """Probabilidade de alvo para cada linha."""
    from statsmodels.tools.tools import add_constant

    if ajuste is None or X is None or len(X) == 0:
        return None
    try:
        return np.asarray(ajuste.predict(add_constant(X.values, has_constant="add")))
    except Exception:
        return None


def embaralhar_rotulos(y: pd.Series, semente: int = 0) -> pd.Series:
    """Permuta os rotulos preservando a distribuicao das classes.

    Preservar a proporcao e o ponto: destrói-se a associacao entre atributo e
    rotulo, e nada mais. Um embaralhamento que tambem alterasse as frequencias
    compararia duas coisas diferentes, e a linha de base perderia sentido.
    """
    rng = np.random.default_rng(semente)
    valores = pd.Series(y).to_numpy().copy()
    rng.shuffle(valores)
    return pd.Series(valores, index=pd.Series(y).index)


@dataclass
class ResultadoModelo:
    """Saida de uma execucao do classificador."""

    convergiu: bool = False
    n_treino: int = 0
    n_teste: int = 0
    coeficientes: Dict[str, float] = field(default_factory=dict)
    dist_classes: Dict[str, float] = field(default_factory=dict)
    razao_chances_geral: Optional[float] = None
    razao_chances_decidido: Optional[float] = None
    backtest: object = None
    n_decidido: int = 0

    @property
    def classe_unica(self) -> bool:
        d = self.dist_classes or {}
        presentes = [k for k in ("alvo", "stop", "tempo") if float(d.get(k, 0.0)) > 0.0]
        return len(presentes) <= 1


@dataclass
class AvaliacaoH14:
    """Um par, com as tres linhas de base: regras, embaralhado e buy-and-hold."""

    par: str
    modelo: ResultadoModelo = None
    embaralhado: ResultadoModelo = None
    regras: object = None
    validacao_modelo: object = None
    validacao_regras: object = None
    retorno_sem_custo_modelo: Optional[float] = None
    retorno_sem_custo_regras: Optional[float] = None
    n_purgadas: int = 0
    n_embargadas: int = 0
    status: str = "inconclusivo"
    motivo: str = ""

    def _bt(self):
        return self.modelo.backtest if self.modelo is not None else None

    def _delta(self, atributo: str) -> float:
        bt, reg = self._bt(), self.regras
        if bt is None or reg is None:
            return 0.0
        return getattr(bt, atributo) - getattr(reg, atributo)

    @property
    def delta_retorno(self) -> float:
        return self._delta("total_return_pct")

    @property
    def delta_drawdown(self) -> float:
        return self._delta("max_drawdown_pct")

    @property
    def delta_exposicao(self) -> float:
        return self._delta("exposure_pct")

    @property
    def delta_operacoes(self) -> int:
        return int(self._delta("total_trades"))

    @property
    def delta_timing(self) -> float:
        """Ganho descontada a exposicao, modelo menos regras (M7)."""
        return ganho_de_timing(self._bt()) - ganho_de_timing(self.regras)

    @property
    def delta_vs_embaralhado(self) -> float:
        """A grandeza que decide se ha SINAL.

        As demais respondem "o modelo e melhor que as regras?". So esta responde
        "o que o modelo achou esta nos dados ou na capacidade dele?".
        """
        if self.embaralhado is None:
            return 0.0
        return ganho_de_timing(self._bt()) - ganho_de_timing(self.embaralhado.backtest)

    @property
    def delta_timing_validacao(self) -> Optional[float]:
        if self.validacao_modelo is None or self.validacao_regras is None:
            return None
        return ganho_de_timing(self.validacao_modelo) - ganho_de_timing(self.validacao_regras)

    @property
    def delta_custo(self) -> float:
        bt, reg = self._bt(), self.regras
        if (bt is None or reg is None or self.retorno_sem_custo_modelo is None
                or self.retorno_sem_custo_regras is None):
            return 0.0
        return ((bt.total_return_pct - self.retorno_sem_custo_modelo)
                - (reg.total_return_pct - self.retorno_sem_custo_regras))

    @property
    def supera_empate(self) -> bool:
        r = self.modelo.razao_chances_decidido if self.modelo else None
        return r is not None and r > limiar_de_empate()


def limiar_de_empate(params: Optional[ParametrosBarreira] = None) -> float:
    """Razao de chances alvo/stop que zera a expectativa. 1,5/3,0 = 0,500."""
    return (params or ParametrosBarreira()).razao_de_empate


def classificar_avaliacao(a: AvaliacaoH14):
    """Veredito. A ORDEM das checagens e o conteudo da regra.

    Cada posicao veio de um defeito real do registro, e trocar duas de lugar
    reintroduz o defeito correspondente.
    """
    m, e, reg = a.modelo, a.embaralhado, a.regras

    if m is None or reg is None or m.backtest is None:
        return "erro", "uma das versoes nao produziu resultado"

    # Sem modelo estimado nao ha o que julgar. Metricas calculadas sobre uma
    # estimacao que falhou seriam silenciosamente invalidas (FR-012).
    if not m.convergiu:
        return "nao_convergiu", "a estimacao nao convergiu"

    if m.classe_unica:
        return "classe_unica", "todos os eventos na mesma classe: nada a classificar"

    if m.n_treino < MIN_TREINO:
        return ("inconclusivo",
                f"treino com {m.n_treino} amostras apos a purga, "
                f"abaixo do minimo de {MIN_TREINO}")

    for nome, r in (("modelo", m.backtest), ("regras", reg)):
        if r.total_trades < EDGE_MIN_TRADES:
            return ("inconclusivo",
                    f"versao {nome} com {r.total_trades} operacoes, "
                    f"abaixo do minimo de {EDGE_MIN_TRADES}")

    # A guarda que torna tudo o mais interpretavel: se o modelo com rotulos
    # PERMUTADOS alcanca o mesmo desempenho, o que se mediu foi ajuste a ruido.
    if e is not None and a.delta_vs_embaralhado <= MARGEM_VS_EMBARALHADO_PP:
        return ("sem_sinal",
                f"nao se distingue do modelo de rotulos embaralhados "
                f"({a.delta_vs_embaralhado:+.2f}pp de ganho de timing, margem "
                f"{MARGEM_VS_EMBARALHADO_PP:.1f}pp)")

    # Ha sinal. Ele paga as barreiras?
    empate = limiar_de_empate()
    if not a.supera_empate:
        r = m.razao_chances_decidido
        return ("insuficiente",
                f"sinal detectavel porem insuficiente: razao de chances no "
                f"subconjunto decidido {r if r is None else f'{r:.3f}'} nao "
                f"supera a razao de empate {empate:.3f}")

    if a.delta_drawdown > 0:
        return ("piora",
                f"drawdown subiu ({reg.max_drawdown_pct:.2f}% -> "
                f"{m.backtest.max_drawdown_pct:.2f}%)")

    if a.delta_timing <= 0:
        return ("sem_vantagem",
                f"ganho desaparece ao descontar exposicao "
                f"({a.delta_exposicao:+.1f}pp de exposicao, "
                f"{a.delta_timing:+.2f}pp de timing)")

    # Guarda M11: sobre base perdedora, operar menos aproxima de zero.
    if reg.total_return_pct <= 0:
        return ("confundido",
                f"as regras perdem {reg.total_return_pct:.2f}%: operar menos "
                f"aproxima de zero e isso NAO e vantagem")

    dv = a.delta_timing_validacao
    if dv is None:
        return "inconclusivo", "sem janela de validacao"

    if dv <= 0:
        return ("so_na_busca",
                f"melhorou na busca ({a.delta_timing:+.2f}pp) e nao se sustentou "
                f"fora dela ({dv:+.2f}pp)")

    return ("melhora",
            f"supera regras, embaralhado ({a.delta_vs_embaralhado:+.2f}pp) e a "
            f"razao de empate, com confirmacao fora da amostra ({dv:+.2f}pp)")


__all__ = [
    "MARGEM_VS_EMBARALHADO_PP",
    "MIN_TREINO",
    "AvaliacaoH14",
    "ResultadoModelo",
    "classificar_avaliacao",
    "embaralhar_rotulos",
    "estimar",
    "limiar_de_decisao",
    "limiar_de_empate",
    "prever",
]
