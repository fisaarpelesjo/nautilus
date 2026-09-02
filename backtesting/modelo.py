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
from typing import Callable, Dict, Optional

import numpy as np
import pandas as pd

from backtesting.volatilidade import ganho_de_timing
from config.settings import EDGE_MIN_TRADES
from strategy.barreira_tripla import (
    ATRIBUTOS,
    ParametrosBarreira,
    distribuicao_classes,
    extrair_atributos,
    razao_de_chances,
    rotular,
)
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
    n_alvo_decidido: int = 0
    n_stop_decidido: int = 0

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
        """Exige que o limite inferior do IC supere o empate, nao a estimativa
        pontual -- ver `supera_empate_com_confianca`."""
        m = self.modelo
        if m is None:
            return False
        return supera_empate_com_confianca(m.n_alvo_decidido, m.n_stop_decidido)


def supera_empate_com_confianca(
    alvo: int,
    stop: int,
    params: Optional[ParametrosBarreira] = None,
    confianca: float = 0.95,
) -> bool:
    """Se a razao de chances supera o empate ALEM DA INCERTEZA amostral.

    Comparar a estimativa pontual contra o limiar converte ruido em aprovacao.
    Medido na execucao real de H14: razao pooled de 0,5134 contra empate de
    0,500, com 536 alvos e 1044 stops -- diferenca de MEIO erro padrao,
    p = 0,318. O ponto estimado passava; a evidencia nao existia.

    A checagem correta usa o limite inferior do intervalo de confianca da
    fracao de alvos. No exemplo acima esse limite da razao 0,4696, abaixo do
    empate -- e o veredito muda de "supera" para "nao supera".

    Mesma familia de M9 (amostra insuficiente lida como reprovacao) e de M11
    (encolher lido como vantagem): um numero que parece bom porque a regua nao
    tem tolerancia.
    """
    from statsmodels.stats.proportion import proportion_confint

    n = int(alvo) + int(stop)
    if n <= 0 or alvo <= 0:
        return False

    empate = limiar_de_empate(params)
    # Fracao de alvos equivalente ao empate: razao r <=> fracao r/(1+r).
    fracao_empate = empate / (1.0 + empate)

    inferior, _ = proportion_confint(int(alvo), n, alpha=1 - confianca,
                                    method="wilson")
    return bool(inferior > fracao_empate)


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


# ------------------------------------------------------ avaliacao por par

def _sinais_do_modelo(prob, indice, limiar: float):
    """Serie de sinais a partir das probabilidades previstas.

    BUY onde a probabilidade supera o limiar; HOLD no resto. NAO emite SELL: a
    saida acontece por stop ou alvo, que e exatamente o que os rotulos de
    barreira tripla codificam. Emitir SELL por probabilidade baixa mediria uma
    regra de saida que a rotulagem nao treinou.
    """
    from strategy.base import Signal

    return pd.Series(
        [Signal.BUY if pr > limiar else Signal.HOLD for pr in prob],
        index=indice,
    )


def _simular_com_sinais(prep, estrategia, sinais, **kwargs):
    """Simula com sinais EXTERNOS.

    Chama `simulate_backtest` diretamente em vez de `horizonte._simular`: aquele
    calcula os proprios sinais e ja passa `precomputed_signals`, entao repassar
    o argumento colidiria. A colisao virava TypeError engolido pelo `try` de
    `_simular` e produzia `backtest=None` silenciosamente -- achado no teste de
    fumaca em dado real.
    """
    from backtesting.engine import simulate_backtest
    from backtesting.horizonte import aquecimento_candles

    if prep is None or len(prep) < aquecimento_candles() + 10:
        return None
    try:
        return simulate_backtest(prep, estrategia,
                                 start_index=aquecimento_candles(),
                                 precomputed_signals=sinais, **kwargs)
    except Exception as exc:
        log.warning(f"simulacao com sinais falhou: {type(exc).__name__}: {str(exc)[:60]}")
        return None


def _resultado_modelo(prob, eventos_teste, prep_teste, estrategia, limiar, div,
                      n_treino, coef, **kwargs):
    """Monta o `ResultadoModelo` a partir das previsoes sobre a janela de teste."""

    decide = prob > limiar
    bruto_teste = eventos_teste["rotulo_bruto"]

    r = ResultadoModelo(
        convergiu=True,
        n_treino=n_treino,
        n_teste=int(len(eventos_teste)),
        coeficientes=coef,
        dist_classes=distribuicao_classes(bruto_teste),
        razao_chances_geral=razao_de_chances(bruto_teste),
        razao_chances_decidido=razao_de_chances(bruto_teste[decide]),
        n_decidido=int(decide.sum()),
        n_alvo_decidido=int((bruto_teste[decide] == 1).sum()),
        n_stop_decidido=int((bruto_teste[decide] == -1).sum()),
    )
    sinais = _sinais_do_modelo(prob, prep_teste.index, limiar)
    r.backtest = _simular_com_sinais(prep_teste, estrategia, sinais, **kwargs)
    return r


def avaliar_par(
    par: str,
    params: Optional[ParametrosBarreira] = None,
    df=None,
    eventos_globais=None,
    atributos: Optional[list] = None,
    extrair_atributos_fn: Optional[Callable[[pd.DataFrame], pd.DataFrame]] = None,
) -> AvaliacaoH14:
    """Avalia um par contra as tres linhas de base.

    `eventos_globais` carrega os eventos de TODOS os pares, e e o que permite a
    purga ser global (D4). Passar apenas os deste par reintroduziria o vazamento
    entre pares correlacionados a 0,71.

    `atributos`/`extrair_atributos_fn` (spec 034, H17): permitem avaliar um
    conjunto de atributos diferente do declarado de H14, sem alterar o
    resultado publicado -- o default de cada um e exatamente `ATRIBUTOS`/
    `extrair_atributos`, os mesmos usados por `run_modelo_scan()` quando
    chamado sem esses parametros. Testado explicitamente em
    tests/test_modelo.py (zero mudanca no caminho default).
    """
    from backtesting.horizonte import _simular, preparar
    from backtesting.purga import dividir_com_purga
    from config.settings import TIMEFRAME
    from data.fetcher import fetch_ohlcv
    from strategy.ema_rsi import EmaRsiStrategy

    p = params or ParametrosBarreira()
    atributos = atributos if atributos is not None else ATRIBUTOS
    extrair_atributos_fn = extrair_atributos_fn or extrair_atributos
    a = AvaliacaoH14(par=par)
    estrategia = EmaRsiStrategy()

    if df is None:
        try:
            df = fetch_ohlcv(par, TIMEFRAME, 6000)  # D1, specs/036-historico-estendido/research.md
        except Exception as exc:
            a.status, a.motivo = "erro", f"historico indisponivel: {type(exc).__name__}"
            return a

    prep = preparar(df, estrategia)
    if prep is None:
        a.status, a.motivo = "erro", "indicadores nao puderam ser calculados"
        return a

    rotulos = rotular(prep, p)
    X = extrair_atributos_fn(prep)
    validos = rotulos["rotulo"].notna() & X.notna().all(axis=1)
    if not validos.any():
        a.status, a.motivo = "erro", "nenhum evento rotulavel"
        return a

    eventos = rotulos[validos].copy()
    eventos["par"] = par
    for col in atributos:
        eventos[col] = X.loc[validos, col]

    # A purga enxerga TODOS os pares quando `eventos_globais` e fornecido.
    base_purga = eventos if eventos_globais is None else eventos_globais
    try:
        div = dividir_com_purga(base_purga, ratio_teste=0.3,
                                embargo_velas=p.limite_velas)
    except ValueError as exc:
        a.status, a.motivo = "erro", str(exc)[:80]
        return a

    a.n_purgadas, a.n_embargadas = div.n_purgadas, div.n_embargadas

    treino = base_purga.loc[div.indices_treino]
    teste_deste_par = eventos[eventos["instante"] >= div.inicio_teste]
    if len(treino) < MIN_TREINO or len(teste_deste_par) < EDGE_MIN_TRADES:
        a.modelo = ResultadoModelo(convergiu=True, n_treino=int(len(treino)),
                                   n_teste=int(len(teste_deste_par)),
                                   dist_classes=distribuicao_classes(
                                       teste_deste_par["rotulo_bruto"]))
        a.status, a.motivo = classificar_avaliacao(a)
        return a

    prep_teste = prep.loc[teste_deste_par.index]
    limiar = limiar_de_decisao(p)

    # Linha de base 1: as regras, sobre a MESMA janela de teste.
    a.regras = _simular(prep_teste, estrategia)

    for nome, y in (("modelo", treino["rotulo"]),
                    ("embaralhado", embaralhar_rotulos(treino["rotulo"], semente=42))):
        ajuste = estimar(treino[atributos], y)
        if ajuste is None:
            setattr(a, nome, ResultadoModelo(convergiu=False,
                                             n_treino=int(len(treino))))
            continue
        prob = prever(ajuste, teste_deste_par[atributos])
        if prob is None:
            setattr(a, nome, ResultadoModelo(convergiu=False,
                                             n_treino=int(len(treino))))
            continue
        coef = dict(zip(["const"] + atributos,
                        [float(v) for v in ajuste.params], strict=False))
        setattr(a, nome, _resultado_modelo(
            prob, teste_deste_par, prep_teste, estrategia, limiar, div,
            int(len(treino)), coef))

    # E6 -- custo de giro.
    if a.modelo is not None and a.modelo.convergiu:
        ajuste = estimar(treino[atributos], treino["rotulo"])
        prob = prever(ajuste, teste_deste_par[atributos]) if ajuste else None
        if prob is not None:
            sc = _simular_com_sinais(
                prep_teste, estrategia,
                _sinais_do_modelo(prob, prep_teste.index, limiar),
                fee_rate=0.0, slippage_pct=0.0)
            a.retorno_sem_custo_modelo = sc.total_return_pct if sc else None
    sc_reg = _simular(prep_teste, estrategia, fee_rate=0.0, slippage_pct=0.0)
    a.retorno_sem_custo_regras = sc_reg.total_return_pct if sc_reg else None

    a.status, a.motivo = classificar_avaliacao(a)
    return a


def coletar_eventos(pares, params: Optional[ParametrosBarreira] = None):
    """Eventos rotulados de TODOS os pares, para a purga global (D4)."""
    from backtesting.horizonte import preparar
    from config.settings import TIMEFRAME
    from data.fetcher import fetch_ohlcv
    from strategy.ema_rsi import EmaRsiStrategy

    p = params or ParametrosBarreira()
    estrategia = EmaRsiStrategy()
    partes, series = [], {}

    for par in pares:
        try:
            df = fetch_ohlcv(par, TIMEFRAME, 6000)  # D1, specs/036-historico-estendido/research.md
        except Exception as exc:
            log.warning(f"{par}: {type(exc).__name__}: {str(exc)[:60]}")
            continue
        prep = preparar(df, estrategia)
        if prep is None:
            continue
        series[par] = df
        rot = rotular(prep, p)
        X = extrair_atributos(prep)
        val = rot["rotulo"].notna() & X.notna().all(axis=1)
        if not val.any():
            continue
        ev = rot[val].copy()
        ev["par"] = par
        for col in ATRIBUTOS:
            ev[col] = X.loc[val, col]
        partes.append(ev)

    globais = pd.concat(partes, ignore_index=True) if partes else pd.DataFrame()
    return globais, series


def run_modelo_scan(pares=None, params: Optional[ParametrosBarreira] = None):
    """Avalia cada par contra as tres linhas de base.

    Os eventos sao coletados de todos os pares ANTES da avaliacao, para que a
    purga seja global. Uma falha isolada vira `erro` e a varredura continua.
    """
    from backtesting.horizonte import UNIVERSO_H11

    pares = pares if pares is not None else UNIVERSO_H11
    p = params or ParametrosBarreira()

    globais, series = coletar_eventos(pares, p)
    saida = []
    for par in pares:
        try:
            saida.append(avaliar_par(par, p, df=series.get(par),
                                     eventos_globais=globais if len(globais) else None))
        except Exception as exc:
            log.warning(f"{par}: {type(exc).__name__}: {str(exc)[:60]}")
            saida.append(AvaliacaoH14(par=par, status="erro",
                                      motivo=f"{type(exc).__name__}: {str(exc)[:60]}"))
    return saida


def resumo_agregado(avaliacoes, params: Optional[ParametrosBarreira] = None) -> dict:
    """Resposta agregada de H14, sobre todos os pares de uma vez.

    POR QUE AGREGAR

    O modelo e UNICO e treinado sobre os pares agrupados (D4). Avalia-lo par a
    par fragmenta esse modelo em amostras pequenas demais para julgar: medido,
    a linha de base de regras faz 1 a 9 operacoes na janela de teste de cada
    par, nunca as 10 do minimo, e as doze avaliacoes voltam `inconclusivo` por
    amostra. A unidade natural de avaliacao de um modelo global e o conjunto.

    O QUE SE AGREGA, E O QUE NAO

    Agrega-se o que soma: contagens de operacoes e de desfechos. A razao de
    chances pooled sai das contagens brutas -- soma de alvos sobre soma de
    stops -- e nao da media das razoes por par, que daria peso igual a um par
    com 2 decisoes e a outro com 200.

    NAO se agrega drawdown: ele depende da trajetoria conjunta de capital, que
    exigiria um motor de carteira. Somar ou promediar drawdowns de series
    diferentes produziria um numero sem significado.
    """
    p = params or ParametrosBarreira()
    validas = [a for a in avaliacoes if a.modelo is not None and a.modelo.convergiu]

    def pooled(pegar):
        alvo = sum(getattr(pegar(a), "n_alvo_decidido", 0) for a in validas if pegar(a))
        stop = sum(getattr(pegar(a), "n_stop_decidido", 0) for a in validas if pegar(a))
        razao = (float("inf") if stop == 0 and alvo > 0
                 else (None if stop == 0 else alvo / stop))
        return {"alvo": alvo, "stop": stop, "razao": razao}

    mod = pooled(lambda a: a.modelo)
    emb = pooled(lambda a: a.embaralhado)

    trades = {
        "modelo": sum(a.modelo.backtest.total_trades for a in validas
                      if a.modelo.backtest),
        "embaralhado": sum(a.embaralhado.backtest.total_trades for a in validas
                           if a.embaralhado and a.embaralhado.backtest),
        "regras": sum(a.regras.total_trades for a in validas if a.regras),
    }

    empate = limiar_de_empate(p)
    return {
        "n_pares": len(validas),
        "razao_empate": empate,
        "modelo": mod,
        "embaralhado": emb,
        "trades": trades,
        "supera_empate": supera_empate_com_confianca(mod["alvo"], mod["stop"], p),
        "supera_empate_pontual": mod["razao"] is not None and mod["razao"] > empate,
        "supera_embaralhado": (
            mod["razao"] is not None and emb["razao"] is not None
            and mod["razao"] > emb["razao"]),
    }


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
    "avaliar_par",
    "coletar_eventos",
    "prever",
    "resumo_agregado",
    "supera_empate_com_confianca",
    "run_modelo_scan",
]
