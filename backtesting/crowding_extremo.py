"""H35 -- crowding via long/short ratio e open interest (crowding de
posicionamento, nao de custo de posicao). Aposta CONTRARIA a posicao
majoritaria: long/short ratio no decil mais BAIXO do proprio par (crowded
short, minoria de contas compradas) como gatilho de entrada LONG contraria
(squeeze), confirmada por open interest acima da mediana de treino (capital
real comprometido, nao ruido de poucas contas). Avaliada pela mesma
barreira tripla que H14/H26 ja usam.
`specs/071-h35-crowding-long-short/research.md` declara D1-D6 antes de
medir:

D1: limiar de "crowded short" = decil mais baixo (10%) da distribuicao de
long/short ratio do PROPRIO par -- nao um valor absoluto compartilhado.

D2: confirmacao por open interest (USD) acima da MEDIANA da janela de
treino do proprio par no mesmo instante -- sem isso, ratio extremo com
pouco capital comprometido seria indistinguivel de ruido.

D3: so o lado long -- bot e long-only (CLAUDE.md).

D4: alinhamento long/short-ratio -> candle e open-interest -> candle por
forward-fill causal; candles anteriores ao INICIO REAL do historico de
qualquer uma das duas series sao DESCARTADOS, nunca preenchidos
retroativamente a partir do primeiro valor existente.

D5: limiar (decil) e mediana calibrados SO no treino, aplicados SEM
reajuste na validacao; significancia via supera_empate_com_confianca
(Wilson CI) sobre a contagem AGREGADA (pooled) entre pares.

D6: retencao real do endpoint MEDIDA (nao presumida) -- probe empirico
2026-09-06 mediu ~31 dias (186 candles de 4h) para BTC/USDT:USDT,
independente do timeframe pedido -- ~11x menor que os 2.000 candles de
funding rate usados por H8/H14/H26. `avaliar_par` mede a retencao real por
par (pode variar) em vez de presumir o valor do probe.

Diferente de H8/H23/H24 (carry continuo, aposta A FAVOR do sinal
observado) -- esta e uma aposta CONTRA o sinal, orientada a
posicionamento extremo, pertencente a familia DIRECIONAL que ja falhou em
22 avaliacoes anteriores deste registro (H34 incluida, S6.3-b). Expectativa
honesta declarada: REPROVADA ou INCONCLUSIVA por amostra (dado D6) sao os
resultados mais provaveis.
"""
from dataclasses import dataclass
from typing import List, Optional, Sequence

import pandas as pd

from backtesting.horizonte import UNIVERSO_H11, preparar
from backtesting.modelo import ParametrosBarreira, limiar_de_empate, supera_empate_com_confianca
from backtesting.validation import DEFAULT_VALIDATION_RATIO
from config.settings import TIMEFRAME
from data.fetcher import fetch_ohlcv
from data.long_short_ratio import fetch_long_short_ratio_history, fetch_open_interest_history
from strategy.barreira_tripla import rotular
from strategy.ema_rsi import EmaRsiStrategy

PERCENTIL_EXTREMO = 0.10  # decil mais baixo do long/short ratio -- D1
N_CANDLES = 1000  # cobre com folga a janela real de retencao do endpoint (D6)


@dataclass
class ResultadoParH35:
    par: str
    retencao_dias: float
    limiar_ratio: float
    mediana_oi: float
    n_treino: int
    n_eventos_treino: int
    n_validacao: int
    n_eventos_validacao: int
    alvo_validacao: int
    stop_validacao: int
    razao_validacao: float
    supera_empate_validacao: bool


def _candles_confirmados(
    indice: pd.Index, ratio: pd.Series, oi: pd.Series, limiar_ratio: float, mediana_oi: float,
) -> pd.Index:
    """Instantes de `indice` em que o long/short ratio alinhado (forward-fill
    causal -- D4) fica ABAIXO do limiar (crowded short) E o open interest
    alinhado fica ACIMA da mediana -- as DUAS confirmacoes sao exigidas
    (D2), nunca uma sozinha."""
    ratio_alinhado = ratio.reindex(indice, method="ffill")
    oi_alinhado = oi.reindex(indice, method="ffill")
    confirmado = (ratio_alinhado < limiar_ratio) & (oi_alinhado > mediana_oi)
    return indice[confirmado.fillna(False)]


def avaliar_par(par: str, params: Optional[ParametrosBarreira] = None) -> Optional[ResultadoParH35]:
    """`None` quando o par nao tem mercado perpetuo, uma das duas series nao
    tem dado, ou a janela real disponivel (D6) nao da para dividir
    treino/validacao."""
    p = params or ParametrosBarreira()

    ratio_df = fetch_long_short_ratio_history(par, timeframe=TIMEFRAME)
    oi_df = fetch_open_interest_history(par, timeframe=TIMEFRAME)
    if len(ratio_df) == 0 or len(oi_df) == 0:
        return None
    ratio_serie = ratio_df["longShortRatio"]
    oi_serie = oi_df["openInterestValue"]

    # Inicio real = o MAIOR dos dois inicios -- so a partir dali as DUAS
    # confirmacoes de D2 existem simultaneamente (D4).
    inicio_real = max(ratio_serie.index.min(), oi_serie.index.min())
    retencao_dias = (ratio_serie.index.max() - inicio_real).total_seconds() / 86400

    # Indicadores calculados sobre a serie COMPLETA buscada (warmup real de
    # EMA/ATR), so depois cortada para o inicio real das duas series -- evita
    # gastar candles da janela curta (D6) com aquecimento de indicador.
    df = fetch_ohlcv(par, TIMEFRAME, N_CANDLES)
    prep = preparar(df, EmaRsiStrategy())
    if prep is None or "atr" not in prep.columns:
        return None
    prep = prep[prep.index >= inicio_real]

    corte = int(len(prep) * (1 - DEFAULT_VALIDATION_RATIO))
    if corte <= 0 or corte >= len(prep):
        return None
    idx_treino = prep.index[:corte]
    idx_validacao = prep.index[corte:]

    ratio_treino = ratio_serie.reindex(idx_treino, method="ffill").dropna()
    oi_treino = oi_serie.reindex(idx_treino, method="ffill").dropna()
    if len(ratio_treino) == 0 or len(oi_treino) == 0:
        return None
    limiar_ratio = float(ratio_treino.quantile(PERCENTIL_EXTREMO))
    mediana_oi = float(oi_treino.median())

    rot = rotular(prep, p)["rotulo_bruto"]

    eventos_treino = _candles_confirmados(idx_treino, ratio_serie, oi_serie, limiar_ratio, mediana_oi)
    eventos_validacao = _candles_confirmados(idx_validacao, ratio_serie, oi_serie, limiar_ratio, mediana_oi)

    rot_validacao = rot.loc[eventos_validacao].dropna()
    n_alvo = int((rot_validacao == 1).sum())
    n_stop = int((rot_validacao == -1).sum())
    razao = n_alvo / n_stop if n_stop else float("inf")
    sig = supera_empate_com_confianca(n_alvo, n_stop, p) if n_stop else False

    return ResultadoParH35(
        par=par, retencao_dias=retencao_dias, limiar_ratio=limiar_ratio, mediana_oi=mediana_oi,
        n_treino=len(idx_treino), n_eventos_treino=len(eventos_treino),
        n_validacao=len(idx_validacao), n_eventos_validacao=len(eventos_validacao),
        alvo_validacao=n_alvo, stop_validacao=n_stop, razao_validacao=razao,
        supera_empate_validacao=sig,
    )


def avaliar_universo(pares: Optional[Sequence[str]] = None,
                      params: Optional[ParametrosBarreira] = None) -> List[ResultadoParH35]:
    pares = list(pares) if pares is not None else list(UNIVERSO_H11)
    resultados = []
    for par in pares:
        r = avaliar_par(par, params)
        if r is not None:
            resultados.append(r)
    return resultados


def agregar_pooled(resultados: List[ResultadoParH35],
                    params: Optional[ParametrosBarreira] = None) -> dict:
    """Agrega alvo/stop de validacao entre pares -- mesma logica de pooling
    de H14/H26 (D5): razao de chances so tem poder estatistico agregada."""
    p = params or ParametrosBarreira()
    n_alvo = sum(r.alvo_validacao for r in resultados)
    n_stop = sum(r.stop_validacao for r in resultados)
    razao = n_alvo / n_stop if n_stop else float("inf")
    sig = supera_empate_com_confianca(n_alvo, n_stop, p) if n_stop else False
    return {
        "n_pares": len(resultados), "n_alvo": n_alvo, "n_stop": n_stop,
        "razao": razao, "empate": limiar_de_empate(p), "supera_empate": sig,
    }
