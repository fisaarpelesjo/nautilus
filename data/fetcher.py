import time

import ccxt
import pandas as pd
from config.settings import BINANCE_API_KEY, BINANCE_API_SECRET, CANDLE_LIMIT
from utils.logger import get_logger

log = get_logger("fetcher")

# HTTP 429 (RateLimitExceeded) e 418 (DDoSProtection) sao classes irmas no
# ccxt (ambas sub de NetworkError, nenhuma subclasse da outra) -- as duas
# precisam de retry. Qualquer outro erro (symbol invalido, erro de rede
# generico) propaga imediatamente, sem retry silencioso escondendo um
# problema real. Ver specs/011-rate-limit-hardening/research.md.
_RATE_LIMIT_ERRORS = (ccxt.RateLimitExceeded, ccxt.DDoSProtection)
_MAX_RETRY_ATTEMPTS = 3
_RETRY_BACKOFF_BASE_SECONDS = 1.0

def _call_with_rate_limit_retry(fn, *args, **kwargs):
    for attempt in range(1, _MAX_RETRY_ATTEMPTS + 1):
        try:
            return fn(*args, **kwargs)
        except _RATE_LIMIT_ERRORS:
            if attempt == _MAX_RETRY_ATTEMPTS:
                raise
            wait = _RETRY_BACKOFF_BASE_SECONDS * (2 ** (attempt - 1))
            log.warning(f"Rate limit da Binance, tentativa {attempt}/{_MAX_RETRY_ATTEMPTS}, aguardando {wait}s...")
            time.sleep(wait)

_cache: dict[str, pd.DataFrame] = {}

# Uma instancia de ccxt.binance por modo (sandbox/producao), reusada entre
# chamadas -- instanciar uma nova a cada chamada (comportamento anterior) zera
# o rate-limiter interno do ccxt (enableRateLimit) a cada vez, sem nenhuma
# protecao real contra limite de taxa da Binance. Ver
# specs/011-rate-limit-hardening/research.md.
_exchange_cache: dict[bool, ccxt.binance] = {}

def get_exchange(sandbox: bool = False) -> ccxt.binance:
    if sandbox in _exchange_cache:
        return _exchange_cache[sandbox]
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
    _exchange_cache[sandbox] = exchange
    return exchange

def reset_exchange_cache() -> None:
    """Limpa o cache de instancias de exchange -- uso em testes, para uma
    execucao nao vazar a instancia (e credenciais mockadas) para a proxima."""
    _exchange_cache.clear()

def fetch_ohlcv(symbol: str, timeframe: str, limit: int = CANDLE_LIMIT) -> pd.DataFrame:
    cache_key = f"{symbol}_{timeframe}"
    exchange = get_exchange()

    if cache_key not in _cache:
        log.info(f"Carregando {limit} candles de {symbol} [{timeframe}] (primeira vez)...")
        raw = _call_with_rate_limit_retry(exchange.fetch_ohlcv, symbol, timeframe, limit=limit)
        df = _to_df(raw)
        _cache[cache_key] = df
        log.info(f"Cache carregado: {len(df)} candles")
    else:
        raw = _call_with_rate_limit_retry(exchange.fetch_ohlcv, symbol, timeframe, limit=5)
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
    return _call_with_rate_limit_retry(get_exchange().fetch_ticker, symbol)

def fetch_tickers() -> dict:
    return _call_with_rate_limit_retry(get_exchange().fetch_tickers)

def fetch_balance() -> dict:
    balance = _call_with_rate_limit_retry(get_exchange().fetch_balance)
    return {k: v for k, v in balance["total"].items() if v > 0}

def fetch_order_book(symbol: str, limit: int = 20) -> dict:
    return _call_with_rate_limit_retry(get_exchange().fetch_order_book, symbol, limit=limit)
