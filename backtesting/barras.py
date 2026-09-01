"""H13 -- comparacao pareada entre amostragem por tempo e por informacao.

O QUE ESTE MODULO MEDE

Nao "a versao reamostrada e boa?", mas "ela e melhor que a MESMA estrategia
sobre o MESMO periodo de calendario, amostrado por tempo?". Dai a unidade de
analise ser a comparacao pareada.

A RESTRICAO ESTRUTURAL DESTA HIPOTESE

Barras dirigidas produzem uma QUANTIDADE diferente de observacoes sobre o mesmo
periodo. Comparar 1.532 barras contra 2.000 candles e comparar tamanhos de
amostra, nao esquemas de amostragem. Por isso o limiar e calibrado (D2) ate a
contagem parear, e por isso `n_tempo`/`n_barras` aparecem em toda comparacao.

INERCIA SE MEDE CONTRA A BASE, NAO CONTRA A VERSAO DE TEMPO

Consequencia direta da calibracao: `n_barras ~= n_tempo` e o RESULTADO
DESEJADO. Medir inercia por essa razao marcaria como inerte exatamente o caso
bem calibrado. Inercia e cada candle de BASE ter virado uma barra -- isto e,
`n_barras ~= n_base`.

A MEDIDA DE EXPOSICAO AQUI E TEMPO, NAO CAPITAL

Diferente da spec 025. Mudar a amostragem muda QUANDO as decisoes acontecem, e
portanto os instantes de entrada e saida: a exposicao de tempo responde. Em H12
o mecanismo alterava so o tamanho da posicao, a exposicao de tempo era
invariante por construcao, e por isso M10 exigiu a medida de capital. Ver D4.
"""
from dataclasses import dataclass
from typing import Dict, List, Optional

from backtesting.validation import MIN_WINDOW_CANDLES, split_train_validation
from backtesting.volatilidade import ganho_de_timing
from config.settings import EDGE_MIN_TRADES, TIMEFRAME
from data.bars import ParametrosBarra, calibrar_limiar, construir_barras, diagnostico
from data.fetcher import fetch_ohlcv
from strategy.base import BaseStrategy
from utils.logger import get_logger

log = get_logger("barras")

# Base fina o bastante para as barras terem resolucao, longa o bastante para
# cobrir a mesma janela de calendario do 4h x 2000 usado por todas as hipoteses
# anteriores: 1h x 8000 = 333,3 dias contra 333,2. Ver D1.
BASE_TIMEFRAME = "1h"
BASE_CANDLES = 8000
TEMPO_TIMEFRAME = TIMEFRAME

# Acima disto, cada candle de base virou uma barra e nao ha reamostragem.
PCT_1_CANDLE_INERTE = 90.0
RAZAO_BASE_INERTE = 0.98

# Aquecimento nao pode consumir mais que isto da janela. H11: 50 candles
# semanais eram 350 dias, quase um ano antes da primeira decisao.
MAX_FRACAO_AQUECIMENTO = 0.33

# Buy-and-hold e o unico ponto fixo entre as duas amostragens.
TOLERANCIA_BUY_HOLD_PP = 0.5


@dataclass
class ComparacaoBarras:
    """Uma estrategia sobre um par, nas duas amostragens."""

    estrategia: str
    par: str
    tipo: str = "dollar"
    tempo: object = None
    barras: object = None
    n_base: int = 0
    n_tempo: int = 0
    n_barras: int = 0
    inicio: object = None
    fim: object = None
    dias_janela: float = 0.0
    aquecimento_dias_tempo: float = 0.0
    aquecimento_dias_barras: float = 0.0
    limiar_calibrado: float = 0.0
    pct_barras_1_candle: float = 0.0
    buy_hold_comum: Optional[float] = None
    validacao_tempo: object = None
    validacao_barras: object = None
    retorno_sem_custo_tempo: Optional[float] = None
    retorno_sem_custo_barras: Optional[float] = None
    status: str = "inconclusivo"
    motivo: str = ""

    def _delta(self, atributo: str) -> float:
        if self.tempo is None or self.barras is None:
            return 0.0
        return getattr(self.barras, atributo) - getattr(self.tempo, atributo)

    @property
    def delta_retorno(self) -> float:
        return self._delta("total_return_pct")

    @property
    def delta_drawdown(self) -> float:
        """Negativo significa MENOS drawdown na versao reamostrada."""
        return self._delta("max_drawdown_pct")

    @property
    def delta_exposicao(self) -> float:
        """Exposicao de TEMPO -- a medida certa para este mecanismo (D4)."""
        return self._delta("exposure_pct")

    @property
    def delta_operacoes(self) -> int:
        return int(self._delta("total_trades"))

    @property
    def delta_timing(self) -> float:
        """Variacao do ganho descontada a exposicao de tempo.

        Sem este desconto, uma versao que apenas participa menos num mercado em
        queda apresenta retorno melhor e seria lida como habilidosa (M7).

        Usa `buy_hold_comum` quando disponivel: a referencia e do PERIODO, nao
        da amostragem, e cada versao so produz uma estimativa dela.
        """
        return (ganho_de_timing(self.barras, buy_hold=self.buy_hold_comum)
                - ganho_de_timing(self.tempo, buy_hold=self.buy_hold_comum))

    @property
    def delta_timing_validacao(self) -> Optional[float]:
        if self.validacao_tempo is None or self.validacao_barras is None:
            return None
        return (ganho_de_timing(self.validacao_barras)
                - ganho_de_timing(self.validacao_tempo))

    @property
    def delta_custo(self) -> float:
        if (self.tempo is None or self.barras is None
                or self.retorno_sem_custo_tempo is None
                or self.retorno_sem_custo_barras is None):
            return 0.0
        custo_barras = self.barras.total_return_pct - self.retorno_sem_custo_barras
        custo_tempo = self.tempo.total_return_pct - self.retorno_sem_custo_tempo
        return custo_barras - custo_tempo

    @property
    def razao_observacoes(self) -> float:
        return self.n_barras / self.n_tempo if self.n_tempo else 0.0

    @property
    def buy_hold_divergente(self) -> bool:
        """Sanidade da ancoragem (FR-007).

        Com as janelas alinhadas por calendario, as duas versoes so podem
        divergir por efeito de fronteira de barra -- a primeira e a ultima barra
        de cada amostragem nao caem no mesmo instante. Divergencia ALEM da
        tolerancia significa que o alinhamento falhou, e ai nada e comparavel.
        """
        if self.tempo is None or self.barras is None:
            return False
        return abs(self.barras.buy_hold_return_pct
                   - self.tempo.buy_hold_return_pct) > TOLERANCIA_BUY_HOLD_PP


def classificar_comparacao_barras(c: ComparacaoBarras):
    """Veredito. A ORDEM das checagens e o conteudo da regra.

    Cada posicao nesta sequencia veio de um defeito real do registro, e trocar
    duas de lugar reintroduz o defeito correspondente.
    """
    t, b = c.tempo, c.barras

    if t is None or b is None:
        return "erro", "uma das versoes nao produziu resultado"

    # O buy-and-hold e o unico ponto fixo entre as duas amostragens. Se ele se
    # move, a comparacao esta desancorada e nada nela e comparavel (FR-007).
    if c.buy_hold_divergente:
        return ("erro",
                f"buy-and-hold divergente entre as versoes "
                f"({t.buy_hold_return_pct:.2f}% vs {b.buy_hold_return_pct:.2f}%): "
                f"comparacao desancorada")

    # Inercia precede tudo: se cada candle de base virou uma barra, as duas
    # versoes nao diferem em esquema de amostragem (FR-012, licao de H12).
    if c.pct_barras_1_candle >= PCT_1_CANDLE_INERTE or (
            c.n_base and c.n_barras >= RAZAO_BASE_INERTE * c.n_base):
        return ("inerte",
                f"{c.pct_barras_1_candle:.0f}% das barras tem um candle so: "
                f"a reamostragem nao agrupou nada")

    # Aquecimento em DIAS de calendario, nao em numero de barras (FR-010, H11).
    if c.dias_janela > 0:
        for nome, dias in (("tempo", c.aquecimento_dias_tempo),
                           ("barras", c.aquecimento_dias_barras)):
            if dias > MAX_FRACAO_AQUECIMENTO * c.dias_janela:
                return ("inconclusivo",
                        f"aquecimento da versao {nome} consome {dias:.0f} de "
                        f"{c.dias_janela:.0f} dias da janela")

    # Amostra precede qualquer avaliacao de metrica (FR-011, H10/H11/M9).
    for nome, r in (("tempo", t), ("barras", b)):
        if r.total_trades < EDGE_MIN_TRADES:
            return ("inconclusivo",
                    f"versao {nome} com {r.total_trades} operacoes, "
                    f"abaixo do minimo de {EDGE_MIN_TRADES}")

    if c.delta_drawdown > 0:
        return ("piora",
                f"drawdown subiu ({t.max_drawdown_pct:.2f}% -> "
                f"{b.max_drawdown_pct:.2f}%)")

    if c.delta_drawdown == 0:
        return "sem_vantagem", "drawdown nao mudou"

    if c.delta_timing <= 0:
        return ("sem_vantagem",
                f"drawdown caiu {abs(c.delta_drawdown):.2f}pp mas o ganho "
                f"desaparece ao descontar exposicao "
                f"({c.delta_exposicao:+.1f}pp de exposicao, "
                f"{c.delta_timing:+.2f}pp de timing)")

    # Guarda M11: sobre base perdedora, operar menos aproxima de zero.
    if t.total_return_pct <= 0:
        return ("confundido",
                f"versao de tempo perde {t.total_return_pct:.2f}%: operar menos "
                f"aproxima de zero e isso NAO e vantagem")

    dv = c.delta_timing_validacao
    if dv is None:
        return ("inconclusivo",
                "sem janela de validacao: historico nao comporta o split")

    if dv <= 0:
        return ("so_na_busca",
                f"melhorou na busca ({c.delta_timing:+.2f}pp) e nao se sustentou "
                f"fora dela ({dv:+.2f}pp)")

    return ("melhora",
            f"base lucrativa, timing {c.delta_timing:+.2f}pp na busca e "
            f"{dv:+.2f}pp na validacao fora da amostra")


# ------------------------------------------------------------- varredura (US1)

def _fatia_alinhada(prep, inicio, fim, aquecimento):
    """Fatia que faz a simulacao COMECAR em `inicio` nas duas versoes.

    `_simular` sempre pula `aquecimento` observacoes. Entao a fatia precisa
    incluir exatamente essas observacoes ANTES de `inicio`, para que a primeira
    vela simulada seja a de `inicio` em ambas as amostragens.
    """
    pos = prep.index.searchsorted(inicio)
    ini = max(0, pos - aquecimento)
    fim_pos = prep.index.searchsorted(fim, side="right")
    return prep.iloc[ini:fim_pos]


def _dias(df) -> float:
    try:
        return float((df.index[-1] - df.index[0]).total_seconds()) / 86400.0
    except (AttributeError, TypeError, IndexError):
        return 0.0


def _aquecimento_dias(df, n_aquecimento: int) -> float:
    """Quantos dias de calendario as primeiras `n` observacoes consomem."""
    if df is None or len(df) <= n_aquecimento:
        return float("inf")
    try:
        delta = df.index[n_aquecimento] - df.index[0]
        return float(delta.total_seconds()) / 86400.0
    except (AttributeError, TypeError):
        return 0.0


def comparar_amostragem(
    estrategia: BaseStrategy,
    nome_estrategia: str,
    par: str,
    tipo: str = "dollar",
    params: Optional[ParametrosBarra] = None,
    df_base=None,
) -> ComparacaoBarras:
    """Roda a MESMA estrategia sobre o MESMO periodo, em duas amostragens.

    A versao de tempo e a serie reamostrada a partir da MESMA base de 1h, e nao
    uma busca separada em 4h: assim as duas cobrem exatamente o mesmo intervalo
    de calendario e compartilham o mesmo buy-and-hold (FR-005, FR-007).
    """
    from backtesting.horizonte import (
        _simular, aquecimento_candles, preparar,
    )

    c = ComparacaoBarras(estrategia=nome_estrategia, par=par, tipo=tipo)
    p = params or ParametrosBarra(tipo=tipo)

    if df_base is None:
        try:
            df_base = fetch_ohlcv(par, BASE_TIMEFRAME, BASE_CANDLES)
        except Exception as exc:
            c.status, c.motivo = "erro", f"historico indisponivel: {type(exc).__name__}"
            return c

    c.n_base = len(df_base)
    c.inicio, c.fim = df_base.index[0], df_base.index[-1]
    c.dias_janela = _dias(df_base)

    # Versao de tempo: agrupamento por relogio a partir da MESMA base.
    try:
        # label="right", closed="left": a barra [T, T+4h) e rotulada T+4h, o
        # instante em que fica completa -- mesma convencao de `construir_barras`.
        # O default do pandas rotula pela borda ESQUERDA, e comparar as duas
        # convencoes fazia o mesmo instante ter closes diferentes em cada versao.
        serie_tempo = df_base.resample(
            _regra_pandas(TEMPO_TIMEFRAME), label="right", closed="left",
        ).agg({
            "open": "first", "high": "max", "low": "min",
            "close": "last", "volume": "sum",
        }).dropna()
    except Exception as exc:
        c.status, c.motivo = "erro", f"reamostragem por tempo falhou: {type(exc).__name__}"
        return c

    # Versao por informacao, com limiar calibrado ate parear a contagem (D2).
    try:
        p.barras_alvo = len(serie_tempo)
        c.limiar_calibrado = calibrar_limiar(df_base, tipo, p)
        serie_barras = construir_barras(df_base, tipo, limiar=c.limiar_calibrado)
    except Exception as exc:
        c.status, c.motivo = "erro", f"construcao de barras falhou: {type(exc).__name__}: {str(exc)[:60]}"
        return c

    c.n_tempo, c.n_barras = len(serie_tempo), len(serie_barras)
    c.pct_barras_1_candle = diagnostico(serie_barras)["pct_1_candle"]

    aquecimento = aquecimento_candles()
    c.aquecimento_dias_tempo = _aquecimento_dias(serie_tempo, aquecimento)
    c.aquecimento_dias_barras = _aquecimento_dias(serie_barras, aquecimento)
    c.dias_janela = _dias(df_base)

    prep_tempo = preparar(serie_tempo, estrategia)
    prep_barras = preparar(serie_barras, estrategia)
    if prep_tempo is None or prep_barras is None:
        c.status, c.motivo = "erro", "indicadores nao puderam ser calculados"
        return c

    # ALINHAMENTO DE CALENDARIO (FR-005). Sem isto, `_simular` pula 50
    # observacoes em cada versao, e 50 barras cobrem quantidades DIFERENTES de
    # dias -- medido: 8,3 dias na versao de tempo contra 6,0 na de dollar bars.
    # As simulacoes comecavam em datas diferentes, com precos iniciais
    # diferentes, e portanto buy-and-holds diferentes. Aqui as duas passam a
    # comecar no mesmo instante.
    #
    # O fatiamento acontece DEPOIS de `preparar()`: os indicadores ja estao
    # calculados sobre a serie inteira, entao a fatia carrega aquecimento real
    # em vez de recomeca-lo -- mesma razao documentada em horizonte.preparar.
    if len(prep_tempo) <= aquecimento or len(prep_barras) <= aquecimento:
        c.status, c.motivo = "inconclusivo", "historico nao comporta o aquecimento"
        return c

    # As fronteiras precisam ser instantes presentes nas DUAS series, senao a
    # primeira e a ultima barra de cada amostragem caem em momentos diferentes e
    # o buy-and-hold de cada versao mede um trecho ligeiramente distinto.
    # Medido antes deste ajuste: 0,73pp de divergencia em BTC dollar bars.
    # Como toda fronteira de barra cai numa marca de hora da base, a intersecao
    # dos indices nunca e vazia.
    comuns = prep_tempo.index.intersection(prep_barras.index)
    minimo = max(prep_tempo.index[aquecimento], prep_barras.index[aquecimento])
    maximo = min(prep_tempo.index[-1], prep_barras.index[-1])
    candidatos = comuns[(comuns >= minimo) & (comuns <= maximo)]
    if len(candidatos) < 2:
        c.status, c.motivo = "erro", "janelas nao se sobrepoem em instantes comuns"
        return c
    inicio_comum, fim_comum = candidatos[0], candidatos[-1]

    prep_tempo = _fatia_alinhada(prep_tempo, inicio_comum, fim_comum, aquecimento)
    prep_barras = _fatia_alinhada(prep_barras, inicio_comum, fim_comum, aquecimento)

    # A referencia e do PERIODO, nao da amostragem: calculada uma vez sobre a
    # serie base, no intervalo comum. Cada versao so produziria uma estimativa
    # dela, diferindo por qual barra cai primeiro.
    janela_base = df_base.loc[inicio_comum:fim_comum]
    if len(janela_base) > 1:
        primeiro = float(janela_base["close"].iloc[0])
        if primeiro > 0:
            c.buy_hold_comum = (float(janela_base["close"].iloc[-1]) / primeiro - 1.0) * 100.0
    c.inicio, c.fim = inicio_comum, fim_comum
    c.dias_janela = _dias(janela_base)

    c.tempo = _simular(prep_tempo, estrategia)
    c.barras = _simular(prep_barras, estrategia)

    # E6 -- custo de giro (US4).
    sc_t = _simular(prep_tempo, estrategia, fee_rate=0.0, slippage_pct=0.0)
    sc_b = _simular(prep_barras, estrategia, fee_rate=0.0, slippage_pct=0.0)
    c.retorno_sem_custo_tempo = sc_t.total_return_pct if sc_t else None
    c.retorno_sem_custo_barras = sc_b.total_return_pct if sc_b else None

    # E3 -- confirmacao fora da amostra, mesmo split das demais hipoteses.
    for atributo, prep in (("tempo", prep_tempo), ("barras", prep_barras)):
        _, val = split_train_validation(prep)
        if val is not None and len(val) > aquecimento + 10:
            setattr(c, f"validacao_{atributo}", _simular(val, estrategia))

    c.status, c.motivo = classificar_comparacao_barras(c)
    return c


def _regra_pandas(timeframe: str) -> str:
    """Converte o timeframe do projeto para a regra de reamostragem do pandas."""
    unidades = {"m": "min", "h": "h", "d": "D", "w": "W"}
    numero, sufixo = timeframe[:-1], timeframe[-1].lower()
    return f"{numero}{unidades.get(sufixo, 'h')}"


def run_barras_scan(
    estrategias: Optional[Dict] = None,
    pares: Optional[List[str]] = None,
    tipos: Optional[List[str]] = None,
    params: Optional[ParametrosBarra] = None,
) -> List[ComparacaoBarras]:
    """Varre estrategia x par x tipo de barra.

    Uma combinacao que falha vira `erro` e a varredura continua -- abortar
    perderia as demais por um par sem historico (FR-016).

    A base de 1h e buscada UMA vez por par e reusada entre estrategias e tipos:
    sao 8.000 candles por requisicao e a varredura tem 96 combinacoes.
    """
    from backtesting.horizonte import ESTRATEGIAS_H11, UNIVERSO_H11

    estrategias = estrategias if estrategias is not None else ESTRATEGIAS_H11()
    pares = pares if pares is not None else UNIVERSO_H11
    tipos = tipos if tipos is not None else ["dollar", "cusum"]

    saida: List[ComparacaoBarras] = []
    for par in pares:
        try:
            df_base = fetch_ohlcv(par, BASE_TIMEFRAME, BASE_CANDLES)
        except Exception as exc:
            log.warning(f"{par}: {type(exc).__name__}: {str(exc)[:60]}")
            df_base = None

        for nome, est in estrategias.items():
            for tipo in tipos:
                if df_base is None:
                    saida.append(ComparacaoBarras(
                        estrategia=nome, par=par, tipo=tipo,
                        status="erro", motivo="historico indisponivel"))
                    continue
                try:
                    saida.append(comparar_amostragem(
                        est, nome, par, tipo,
                        ParametrosBarra(tipo=tipo), df_base=df_base))
                except Exception as exc:
                    log.warning(f"{nome} x {par} x {tipo}: "
                                f"{type(exc).__name__}: {str(exc)[:60]}")
                    saida.append(ComparacaoBarras(
                        estrategia=nome, par=par, tipo=tipo, status="erro",
                        motivo=f"{type(exc).__name__}: {str(exc)[:60]}"))
    return saida


__all__ = [
    "MIN_WINDOW_CANDLES",
    "ComparacaoBarras",
    "classificar_comparacao_barras",
    "comparar_amostragem",
    "run_barras_scan",
]
