"""Historico de taxa de financiamento (funding rate) de perpetuos USDT-M na
Binance -- fonte de dados para H8 (arbitragem de funding rate,
specs/058-h8-funding-rate-revisao/). Endpoint futures-only: exchange
separada (`defaultType=future`) da usada por `fetch_ohlcv` (spot), mesmos
padroes de retry/cache de `data/fetcher.py`.
"""
import ccxt
import pandas as pd

from data.fetcher import _call_with_rate_limit_retry
from utils.logger import get_logger

log = get_logger("funding")

# Mesmo teto de ~1000 registros por chamada que `fetch_ohlcv` ja documenta
# para candles -- o endpoint de funding rate da Binance tem o mesmo limite.
_MAX_RECORDS_PER_CALL = 1000

_futures_exchange: ccxt.binance = None


def _get_futures_exchange() -> ccxt.binance:
    global _futures_exchange
    if _futures_exchange is None:
        _futures_exchange = ccxt.binance({
            "enableRateLimit": True,
            "timeout": 10000,
            "options": {"defaultType": "future"},
        })
    return _futures_exchange


def reset_futures_exchange_cache() -> None:
    """Uso em testes -- mesma finalidade de `data.fetcher.reset_exchange_cache`."""
    global _futures_exchange
    _futures_exchange = None


def perp_symbol(par_spot: str) -> str:
    """`BTC/USDT` -> `BTC/USDT:USDT` -- formato ccxt para perpetuo linear."""
    base, quote = par_spot.split("/")
    return f"{base}/{quote}:{quote}"


def fetch_funding_rate_history(par_spot: str, dias: int = 365) -> pd.DataFrame:
    """Historico de funding rate (periodo de 8h) do perpetuo correspondente
    ao par spot, paginado ate cobrir `dias` ou esgotar o historico
    disponivel. Devolve DataFrame vazio (nunca lanca) quando o par nao tem
    mercado perpetuo -- par listado so a vista, ou par novo demais --
    tratado como ausencia de dado, nao erro: o chamador decide se isso
    exclui o par do universo."""
    exchange = _get_futures_exchange()
    symbol = perp_symbol(par_spot)

    ate = exchange.milliseconds()
    desde = ate - dias * 24 * 60 * 60 * 1000

    registros = []
    cursor = desde
    while cursor < ate:
        try:
            lote = _call_with_rate_limit_retry(
                exchange.fetch_funding_rate_history, symbol,
                since=cursor, limit=_MAX_RECORDS_PER_CALL,
            )
        except ccxt.BadSymbol:
            log.info(f"{par_spot}: sem mercado perpetuo correspondente ({symbol})")
            return pd.DataFrame(columns=["fundingRate"])
        if not lote:
            break
        registros += lote
        proximo = lote[-1]["timestamp"] + 1
        if proximo <= cursor:
            break
        cursor = proximo
        if len(lote) < _MAX_RECORDS_PER_CALL:
            break

    if not registros:
        return pd.DataFrame(columns=["fundingRate"])

    df = pd.DataFrame(registros)
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
    df = df.set_index("timestamp")[["fundingRate"]].sort_index()
    df = df[~df.index.duplicated(keep="last")]
    return df
