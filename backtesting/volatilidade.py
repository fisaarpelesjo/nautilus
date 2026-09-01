"""H12 — Dimensionamento de posicao por volatilidade (volatility targeting).

TESE

Alocar valor nocional constante em ativos de volatilidade variavel significa
assumir risco variavel. Escalar a posicao inversamente a volatilidade realizada
mantem a EXPOSICAO AO RISCO aproximadamente constante -- e o mecanismo padrao de
controle de drawdown em gestao sistematica.

MOTIVACAO VEM DE DENTRO DO REGISTRO

H7 (momentum transversal) reprovou com drawdown de 11,76% contra o teto de
10,0%. Profit factor, numero de operacoes e retorno contra buy-and-hold todos
passavam. Foi a UNICA hipotese da investigacao a falhar exclusivamente no limite
de risco. Se o excesso de drawdown for consequencia do dimensionamento, H12
traz H7 de volta para dentro do teto e ela volta a ser testavel.

O TETO DO FATOR E INVARIANTE DE CODIGO

    fator = min(1.0, alvo / atr_ratio)

O `min` nao e validacao defensiva, e a fórmula. FR-003 proibe ampliar a posicao,
e a constituicao do projeto proibe alavancagem (`max_leverage = 1`). Com o teto
aqui, nao existe caminho pelo qual esta feature aumente exposicao -- nem por
alvo mal configurado, nem por volatilidade anormalmente baixa.

POR QUE risk/manager.py NAO E TOCADO

E caminho de producao, sujeito ao principio Safety First. FR-013 exige que o bot
em execucao nao mude enquanto nenhuma hipotese for aprovada. O dimensionamento
vive atras de um parametro opcional de `simulate_backtest` cujo default
reproduz o comportamento atual byte a byte.

O QUE ESTE MODULO MEDE

Nao "a versao dimensionada e boa?", mas "ela e melhor que a MESMA estrategia sem
dimensionamento?". Dai a unidade de analise ser a comparacao pareada, e nao a
combinacao isolada.

E o risco dominante da avaliacao esta declarado na spec: dimensionar por
volatilidade reduz exposicao por construcao -- fator medio 0,90 na medicao de
`research.md`, ou seja ~10% menos exposicao. Num mercado em queda isso sozinho
melhora o retorno relativo ao buy-and-hold sem qualquer capacidade de selecao.
E o achado M7. Por isso `sem_vantagem` existe como estado proprio.
"""
import math
from dataclasses import dataclass, field
from typing import List, Optional

from backtesting.cross_sectional import WalkForwardFold
from config.settings import EDGE_MIN_TRADES, TIMEFRAME
from data.fetcher import fetch_ohlcv
from strategy.base import BaseStrategy
from utils.logger import get_logger

log = get_logger("volatilidade")

# Alvo derivado da mediana observada de `atr_ratio` (0,0187 em 23.412
# observacoes de 4h, 12 pares, 2026-09-01). Escolhido para o mecanismo ser
# NEUTRO NA ESCALA MEDIA, nao para maximizar desempenho: nenhum alvo foi
# testado contra retorno antes de ser fixado. Ver research.md D3.
ALVO_PADRAO = 0.02

# Piso do fator. Evita que volatilidade extrema produza posicao tao pequena que
# a ordem sequer seja aceita pela corretora -- caso de borda da spec.
FATOR_MINIMO_PADRAO = 0.20


@dataclass
class ParametrosVolatilidade:
    alvo: float = ALVO_PADRAO
    fator_minimo: float = FATOR_MINIMO_PADRAO


def fator_volatilidade(atr_ratio, params: Optional[ParametrosVolatilidade] = None) -> float:
    """Multiplicador do tamanho da posicao, em (fator_minimo, 1.0].

        fator = min(1.0, alvo / atr_ratio)

    O `min` e a formula, nao validacao: FR-003 e a proibicao de alavancagem da
    constituicao dependem de nao existir caminho que devolva mais que 1,0.

    `atr_ratio` invalido -- ausente, nulo, negativo ou nao finito -- devolve
    1,0, isto e, o tamanho que o sistema ja calcularia. Recair no vigente e a
    politica de falha do projeto: dado desconhecido nunca vira decisao
    silenciosa, e as alternativas seriam divisao por zero ou posicao infinita.
    """
    p = params or ParametrosVolatilidade()

    try:
        v = float(atr_ratio)
    except (TypeError, ValueError):
        return 1.0

    if not math.isfinite(v) or v <= 0:
        return 1.0

    return max(p.fator_minimo, min(1.0, p.alvo / v))


def ganho_de_timing(resultado) -> float:
    """Retorno descontada a exposicao, em pontos percentuais.

    A definicao vive em `cross_sectional.WalkForwardFold.ganho_de_timing_pp` e e
    reusada aqui construindo um fold, em vez de reescrever a formula. Duas
    definicoes do mesmo conceito no mesmo sistema divergem na primeira correcao
    -- e este conceito especifico e o que separa habilidade de ausencia (M7).
    """
    if resultado is None:
        return 0.0
    return WalkForwardFold(
        janela=0,
        buy_hold_pct=resultado.buy_hold_return_pct,
        retorno_pct=resultado.total_return_pct,
        exposicao_pct=resultado.exposure_pct,
        max_drawdown_pct=resultado.max_drawdown_pct,
        trades=resultado.total_trades,
    ).ganho_de_timing_pp


@dataclass
class ComparacaoPareada:
    """Uma estrategia sobre um par, nas duas versoes.

    H12 nao pergunta "a versao dimensionada e boa?", pergunta "ela e melhor que a
    MESMA estrategia sem dimensionamento?". Dai a unidade de analise ser o par de
    resultados, e nao o resultado isolado.
    """

    estrategia: str
    par: str
    sem_dimensionamento: object = None
    com_dimensionamento: object = None
    folds_base: List = field(default_factory=list)
    folds_dim: List = field(default_factory=list)
    retorno_sem_custo_base: Optional[float] = None
    retorno_sem_custo_dim: Optional[float] = None
    fator_medio: float = 1.0
    status: str = "inconclusivo"
    motivo: str = ""

    def _delta(self, atributo: str) -> float:
        b, d = self.sem_dimensionamento, self.com_dimensionamento
        if b is None or d is None:
            return 0.0
        return getattr(d, atributo) - getattr(b, atributo)

    @property
    def delta_retorno(self) -> float:
        return self._delta("total_return_pct")

    @property
    def delta_drawdown(self) -> float:
        """Negativo significa MENOS drawdown na versao dimensionada."""
        return self._delta("max_drawdown_pct")

    @property
    def delta_exposicao(self) -> float:
        return self._delta("exposure_pct")

    @property
    def delta_operacoes(self) -> int:
        return int(self._delta("total_trades"))

    @property
    def delta_timing(self) -> float:
        """Variacao do ganho ATRIBUIVEL A ESCOLHA, descontada a exposicao.

        E a grandeza que decide entre `melhora` e `sem_vantagem`. Sem ela, uma
        versao que apenas participa menos num mercado em queda apresenta retorno
        melhor e seria lida como habilidosa.
        """
        return ganho_de_timing(self.com_dimensionamento) - ganho_de_timing(self.sem_dimensionamento)

    @property
    def delta_custo(self) -> float:
        """Quanto o custo de execucao pesou a mais (ou a menos) na versao
        dimensionada. Ajustar tamanho implica giro, e giro paga taxa."""
        b, d = self.sem_dimensionamento, self.com_dimensionamento
        if (b is None or d is None
                or self.retorno_sem_custo_base is None
                or self.retorno_sem_custo_dim is None):
            return 0.0
        custo_dim = d.total_return_pct - self.retorno_sem_custo_dim
        custo_base = b.total_return_pct - self.retorno_sem_custo_base
        return custo_dim - custo_base


def classificar_comparacao(c: ComparacaoPareada):
    """Veredito da comparacao. A ORDEM das checagens e o conteudo da regra.

    `inconclusivo` precede qualquer avaliacao de metrica, como em H10 e H11:
    comparar 30 operacoes contra 4 mede diferenca de amostra, nao
    dimensionamento.

    E `sem_vantagem` existe como estado proprio, distinto de `melhora` e de
    `piora`. Colapsa-lo em `melhora` faria H12 passar trivialmente -- o
    mecanismo reduz exposicao por construcao, entao em mercado de queda o
    retorno relativo melhora sozinho.
    """
    b, d = c.sem_dimensionamento, c.com_dimensionamento

    if b is None or d is None:
        return "erro", "uma das versoes nao produziu resultado"

    for nome, r in (("base", b), ("dimensionada", d)):
        if r.total_trades < EDGE_MIN_TRADES:
            return ("inconclusivo",
                    f"versao {nome} com {r.total_trades} operacoes, "
                    f"abaixo do minimo de {EDGE_MIN_TRADES}")

    if c.delta_drawdown >= 0:
        return ("piora",
                f"drawdown nao caiu ({b.max_drawdown_pct:.2f}% -> "
                f"{d.max_drawdown_pct:.2f}%)")

    if c.delta_timing <= 0:
        return ("sem_vantagem",
                f"drawdown caiu {abs(c.delta_drawdown):.2f}pp mas o ganho "
                f"desaparece ao descontar exposicao "
                f"({c.delta_exposicao:+.1f}pp de exposicao, "
                f"{c.delta_timing:+.2f}pp de timing)")

    return ("melhora",
            f"drawdown -{abs(c.delta_drawdown):.2f}pp e timing "
            f"{c.delta_timing:+.2f}pp mesmo descontada a exposicao")


# --------------------------------------------------- varredura pareada (US1)

CANDLES_PADRAO = 2000


class _Sizer:
    """Callable passado a `simulate_backtest`, que registra o que aplicou.

    O fator medio observado nao e telemetria opcional: se ele vier proximo de
    1,0 o mecanismo mal atuou, e um veredito de `sem_vantagem` estaria medindo
    inercia em vez de dimensionamento. Sem esse numero no relatorio nao daria
    para distinguir os dois casos.
    """

    def __init__(self, params: ParametrosVolatilidade):
        self.params = params
        self.fatores: List[float] = []

    def __call__(self, candle) -> float:
        f = fator_volatilidade(candle.get("atr_ratio"), self.params)
        self.fatores.append(f)
        return f

    @property
    def media(self) -> float:
        return sum(self.fatores) / len(self.fatores) if self.fatores else 1.0


def comparar_combinacao(
    estrategia: BaseStrategy,
    nome_estrategia: str,
    par: str,
    horizonte: str = TIMEFRAME,
    params: Optional[ParametrosVolatilidade] = None,
    df=None,
    candles: int = CANDLES_PADRAO,
) -> ComparacaoPareada:
    """Roda a MESMA estrategia sobre a MESMA serie, com e sem dimensionamento.

    Tudo alem do `position_sizer` e mantido identico entre as duas execucoes --
    mesma serie, mesmos indicadores, mesmo fatiamento de walk-forward -- porque
    qualquer outra diferenca contaminaria a atribuicao do resultado ao
    mecanismo.
    """
    from backtesting.horizonte import (
        _simular, _walk_forward_par, derivar_n_janelas, preparar,
    )

    params = params or ParametrosVolatilidade()
    c = ComparacaoPareada(estrategia=nome_estrategia, par=par)

    if df is None:
        try:
            df = fetch_ohlcv(par, horizonte, candles)
        except Exception as exc:
            c.status = "erro"
            c.motivo = f"historico indisponivel: {type(exc).__name__}"
            return c

    preparado = preparar(df, estrategia)
    if preparado is None:
        c.status = "erro"
        c.motivo = "indicadores nao puderam ser calculados"
        return c

    sizer = _Sizer(params)
    c.sem_dimensionamento = _simular(preparado, estrategia)
    c.com_dimensionamento = _simular(preparado, estrategia, position_sizer=sizer)
    c.fator_medio = sizer.media

    # E6 -- custo de giro (US3). Reexecuta as duas versoes com taxa e slippage
    # zerados. Ajustar o tamanho pela volatilidade implica giro, e giro paga
    # taxa: sem separar, um delta de retorno negativo nao distingue "o mecanismo
    # nao ajuda" de "o mecanismo ajuda mas o custo come o ganho".
    sc_base = _simular(preparado, estrategia, fee_rate=0.0, slippage_pct=0.0)
    sc_dim = _simular(preparado, estrategia, fee_rate=0.0, slippage_pct=0.0,
                      position_sizer=_Sizer(params))
    c.retorno_sem_custo_base = sc_base.total_return_pct if sc_base else None
    c.retorno_sem_custo_dim = sc_dim.total_return_pct if sc_dim else None

    n = derivar_n_janelas(len(preparado))
    if n > 0:
        c.folds_base = _walk_forward_par(preparado, estrategia, n)
        c.folds_dim = _walk_forward_par(
            preparado, estrategia, n, position_sizer=_Sizer(params),
        )

    c.status, c.motivo = classificar_comparacao(c)
    return c


def run_volatilidade_scan(
    estrategias: Optional[dict] = None,
    pares: Optional[List[str]] = None,
    horizonte: str = TIMEFRAME,
    params: Optional[ParametrosVolatilidade] = None,
    candles: int = CANDLES_PADRAO,
) -> List[ComparacaoPareada]:
    """Varre estrategia x par. Uma combinacao que falha vira `erro` e a
    varredura continua -- abortar perderia as demais por um par sem historico.
    """
    from backtesting.horizonte import ESTRATEGIAS_H11, UNIVERSO_H11

    estrategias = estrategias if estrategias is not None else ESTRATEGIAS_H11()
    pares = pares if pares is not None else UNIVERSO_H11
    params = params or ParametrosVolatilidade()

    saida: List[ComparacaoPareada] = []
    for nome, est in estrategias.items():
        for par in pares:
            try:
                saida.append(comparar_combinacao(
                    est, nome, par, horizonte, params, candles=candles,
                ))
            except Exception as exc:
                log.warning(f"{nome} x {par}: {type(exc).__name__}: {str(exc)[:60]}")
                saida.append(ComparacaoPareada(
                    estrategia=nome, par=par, status="erro",
                    motivo=f"{type(exc).__name__}: {str(exc)[:60]}",
                ))
    return saida
