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

# Binance limita cada chamada fetch_ohlcv a ~1000 candles por requisicao,
# independente do `limit` pedido -- pedir 2000 retornava silenciosamente so
# os ultimos 1000, sem erro nem aviso. Achado durante a varredura de
# validacao out-of-sample de multiplas estrategias: a janela de confirmacao
# (30% do historico) nunca acumulava os 10 trades minimos exigidos pra
# aprovacao porque o historico real disponivel era metade do que os
# consumidores (backtest/scan/optimize/multimarket, candle_limit=2000)
# assumiam ter. Ver _fetch_ohlcv_paginated().
_EXCHANGE_MAX_CANDLES_PER_CALL = 1000

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
    """Candles OHLCV do simbolo, resolvendo a fonte pelo mercado (spec 023).

    A assinatura NAO muda: os ~10 consumidores existentes (backtest, compare,
    scan, optimize, validation, replay, runner, chart, selector, diagnostics)
    continuam chamando igual e nao sabem qual fonte respondeu.

    Cripto continua indo por `_fetch_ohlcv_ccxt` exatamente como antes -- ver
    tests/test_crypto_no_regression.py, escrito antes deste refactor
    justamente para provar que o caminho nao mudou.
    """
    from data.markets import resolve_market
    from data.sources import get_source

    market = resolve_market(symbol)
    if market.source == "ccxt":
        return _fetch_ohlcv_ccxt(symbol, timeframe, limit)
    return get_source(market.name).fetch_ohlcv(symbol, timeframe, limit)


def _fetch_ohlcv_ccxt(symbol: str, timeframe: str, limit: int = CANDLE_LIMIT) -> pd.DataFrame:
    """Caminho cripto original, extraido sem alteracao de logica.

    Mantido neste modulo (e nao movido para data/sources/ccxt_source.py) porque
    detem o estado global de cache e a instancia de exchange, que a suite ja
    manipula diretamente via `_cache` e `reset_exchange_cache()`.
    """
    cache_key = f"{symbol}_{timeframe}"
    exchange = get_exchange()

    if cache_key not in _cache:
        log.info(f"Carregando {limit} candles de {symbol} [{timeframe}] (primeira vez)...")
        if limit > _EXCHANGE_MAX_CANDLES_PER_CALL:
            raw = _fetch_ohlcv_paginated(exchange, symbol, timeframe, limit)
        else:
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

def _fetch_ohlcv_paginated(exchange: ccxt.binance, symbol: str, timeframe: str, limit: int) -> list:
    """Encadeia chamadas via `since` para superar o teto de ~1000 candles por
    requisicao da Binance, avancando a partir do candle mais antigo ja
    recebido ate reunir `limit` candles ou esgotar o historico disponivel."""
    timeframe_ms = exchange.parse_timeframe(timeframe) * 1000
    since = exchange.milliseconds() - limit * timeframe_ms
    candles: list = []
    while len(candles) < limit:
        batch = _call_with_rate_limit_retry(
            exchange.fetch_ohlcv, symbol, timeframe,
            since=since, limit=_EXCHANGE_MAX_CANDLES_PER_CALL,
        )
        if not batch:
            break
        candles += batch
        next_since = batch[-1][0] + timeframe_ms
        if next_since <= since:
            break  # exchange nao avancou -- evita loop infinito
        since = next_since
        if len(batch) < _EXCHANGE_MAX_CANDLES_PER_CALL:
            break  # lote incompleto = alcancou o presente, sem mais historico
    return candles[-limit:]


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
