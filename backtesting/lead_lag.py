"""H21 -- lead-lag BTC para altcoins (spec 038).

Tese: o retorno do BTC no MESMO candle de 4h que uma altcoin lidera o
retorno dessa altcoin no candle seguinte (causalidade de Granger
unidirecional BTC->altcoins, "Price Transmission from Bitcoin to
Altcoins", Asia-Pacific Financial Markets, Springer 2026). Defasagem e
formula do sinal medidas e declaradas ANTES de qualquer codigo
(specs/038-lead-lag-btc-altcoins/research.md, D1): correlacao maxima e
mais consistente entre os 11 pares (excluindo BTC) em N=1 candle, sem
deslocamento extra.

NAO adiciona atributo ao classificador de H14 (ja fechado reprovado) --
estrategia nova e independente, motor de backtest reusado sem alteracao
(D4): o sinal alimenta `backtesting.modelo._simular_com_sinais`, a mesma
funcao ja usada e testada por H14 para transformar um sinal externo num
BacktestResult.
"""

from typing import Dict, List, Optional, Tuple

import pandas as pd

from backtesting.engine import BacktestResult
from strategy.base import Signal


def btc_retorno_no_candle(btc_close: pd.Series) -> pd.Series:
    """Retorno de fechamento-a-fechamento do BTC no mesmo candle (D1) --
    `close[t]/close[t-1] - 1`, sem deslocamento. Conhecido no exato
    instante em que esse candle fecha, o mesmo instante em que a altcoin
    fecha o seu (grade de 4h alinhada entre pares na mesma exchange) --
    nao ha *lookahead*."""
    return btc_close.pct_change(1)


def _sinais_lead_lag(retorno_btc: pd.Series, indice_par: pd.DatetimeIndex) -> pd.Series:
    """BUY onde o retorno de BTC alinhado ao candle da altcoin e positivo;
    HOLD no resto -- inclusive `NaN` (candle sem retorno de BTC
    correspondente, FR-008) e exatamente zero (D2: sinal binario sobre o
    SINAL do retorno, nao magnitude)."""
    alinhado = retorno_btc.reindex(indice_par)
    return pd.Series(
        [Signal.BUY if v > 0 else Signal.HOLD for v in alinhado],
        index=indice_par,
    )


def avaliar_lead_lag(
    par: str,
    df_alt: Optional[pd.DataFrame] = None,
    retorno_btc: Optional[pd.Series] = None,
) -> Optional[BacktestResult]:
    """Avalia um par contra o sinal de lead-lag do BTC. `df_alt`/
    `retorno_btc` opcionais permitem teste sem rede (mesmo padrao de
    `avaliar_par(df=...)`, H14)."""
    from backtesting.horizonte import preparar
    from backtesting.modelo import _simular_com_sinais
    from config.settings import TIMEFRAME
    from data.fetcher import fetch_ohlcv
    from strategy.ema_rsi import EmaRsiStrategy

    if df_alt is None:
        df_alt = fetch_ohlcv(par, TIMEFRAME, 6000)  # FR-005
    if retorno_btc is None:
        btc_df = fetch_ohlcv("BTC/USDT", TIMEFRAME, 6000)
        retorno_btc = btc_retorno_no_candle(btc_df["close"])

    estrategia = EmaRsiStrategy()
    prep = preparar(df_alt, estrategia)
    if prep is None:
        return None

    sinais = _sinais_lead_lag(retorno_btc, prep.index)
    return _simular_com_sinais(prep, estrategia, sinais)


def resumo_consistencia(resultados: List[Tuple[str, Optional[BacktestResult]]]) -> Dict[str, int]:
    """Quantos pares superam o respectivo buy-and-hold e quantos tem
    profit factor acima de 1,0 -- descritivo, sem veredito agregado novo
    (SC-002)."""
    validos = [r for _, r in resultados if r is not None]
    return {
        "n_pares": len(validos),
        "supera_buy_hold": sum(1 for r in validos if r.total_return_pct > r.buy_hold_return_pct),
        "profit_factor_acima_de_1": sum(1 for r in validos if r.profit_factor > 1.0),
    }


def run_lead_lag_scan(pares: Optional[List[str]] = None):
    """Varre os 11 pares de UNIVERSO_H11 menos BTC/USDT (D3), reusando o
    fetch de BTC/USDT UMA vez entre todos (evita 11 fetches redundantes do
    par-sinal)."""
    from backtesting.approval import evaluate_approval
    from backtesting.horizonte import UNIVERSO_H11
    from config.settings import TIMEFRAME
    from data.fetcher import fetch_ohlcv

    pares = pares if pares is not None else [p for p in UNIVERSO_H11 if p != "BTC/USDT"]

    btc_df = fetch_ohlcv("BTC/USDT", TIMEFRAME, 6000)
    retorno_btc = btc_retorno_no_candle(btc_df["close"])

    saida = []
    for par in pares:
        resultado = avaliar_lead_lag(par, retorno_btc=retorno_btc)
        veredito = evaluate_approval(resultado)
        saida.append((par, resultado, veredito))
    return saida


__all__ = [
    "avaliar_lead_lag",
    "btc_retorno_no_candle",
    "resumo_consistencia",
    "run_lead_lag_scan",
]
