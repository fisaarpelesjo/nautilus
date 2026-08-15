import ccxt
import pandas as pd
from config.settings import BINANCE_API_KEY, BINANCE_API_SECRET, CANDLE_LIMIT
from utils.logger import get_logger

log = get_logger("fetcher")

_cache: dict[str, pd.DataFrame] = {}

def get_exchange(sandbox: bool = False) -> ccxt.binance:
    config = {
        "enableRateLimit": True,
        "timeout": 10000,
        "options": {
            "defaultType": "spot",
            "fetchCurrencies": False,
        },
    }
    # So inclui apiKey/secret quando ambos existem de verdade: passar uma string
    # vazia faz o ccxt tratar a conta como autenticada (self.apiKey is not None)
    # e, em versoes recentes, isso dispara uma chamada privada extra dentro de
    # fetch_markets() (sapiGetEquityMarketExchangeInfo) que falha sem credencial
    # real -- quebrando ate endpoints publicos como fetch_ohlcv em paper mode.
    if BINANCE_API_KEY and BINANCE_API_SECRET:
        config["apiKey"] = BINANCE_API_KEY
        config["secret"] = BINANCE_API_SECRET
    exchange = ccxt.binance(config)
    if sandbox:
        exchange.set_sandbox_mode(True)
    return exchange

def fetch_ohlcv(symbol: str, timeframe: str, limit: int = CANDLE_LIMIT) -> pd.DataFrame:
    cache_key = f"{symbol}_{timeframe}"
    exchange = get_exchange()

    if cache_key not in _cache:
        log.info(f"Carregando {limit} candles de {symbol} [{timeframe}] (primeira vez)...")
        raw = exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
        df = _to_df(raw)
        _cache[cache_key] = df
        log.info(f"Cache carregado: {len(df)} candles")
    else:
        raw = exchange.fetch_ohlcv(symbol, timeframe, limit=5)
        new_df = _to_df(raw)
        df = _cache[cache_key]
        df = pd.concat([df, new_df])
        df = df[~df.index.duplicated(keep="last")]
        df = df.iloc[-limit:]
        _cache[cache_key] = df

    return _cache[cache_key]

def _to_df(raw: list) -> pd.DataFrame:
    df = pd.DataFrame(raw, columns=["timestamp", "open", "high", "low", "close", "volume"])
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
    df.set_index("timestamp", inplace=True)
    return df

def fetch_ticker(symbol: str) -> dict:
    return get_exchange().fetch_ticker(symbol)

def fetch_balance() -> dict:
    balance = get_exchange().fetch_balance()
    return {k: v for k, v in balance["total"].items() if v > 0}

def fetch_order_book(symbol: str, limit: int = 20) -> dict:
    return get_exchange().fetch_order_book(symbol, limit=limit)
