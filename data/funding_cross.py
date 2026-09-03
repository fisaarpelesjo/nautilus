"""Historico de funding rate multi-corretora -- fonte de dados para H24
(diferencial de funding entre corretoras, perp x perp, sem perna a
vista, `specs/061-h24-funding-cross-exchange/`). Mesmo padrao de
`data/funding.py` (paginado, BadSymbol-seguro), parametrizado por
corretora.

Cinco corretoras qualificadas (`research.md` D1, verificado via chamada
real 2026-09-03): binance, bybit, okx, kucoinfutures, gate -- todas
suportam `fetchFundingRateHistory` e tem mercado perpetuo linear
USDT-margined para BTC/USDT e ETH/USDT, mesma cadencia de 8h. Kraken
excluido: `krakenfutures` so oferece BTC/USD (inverso, margeado em
USD/BTC), nunca um perpetuo linear USDT-margined comparavel.
"""
import ccxt
import pandas as pd

from data.fetcher import _call_with_rate_limit_retry
from utils.logger import get_logger

log = get_logger("funding_cross")

_MAX_RECORDS_PER_CALL = 1000

CORRETORAS_QUALIFICADAS = ("binance", "bybit", "okx", "kucoinfutures", "gate")

# Taxa de tomador (futuros, tier base), verificada por busca 2026-09-03
# (research.md D2) -- cada corretora tem a sua, nunca reusa a de outra.
TAXA_TOMADOR = {
    "binance": 0.0005,
    "bybit": 0.00055,
    "okx": 0.0005,
    "kucoinfutures": 0.0006,
    "gate": 0.0005,
}

_CONFIG_CORRETORA = {
    "binance": {"options": {"defaultType": "future"}},
    "bybit": {},
    "okx": {},
    "kucoinfutures": {},
    "gate": {"options": {"defaultType": "swap"}},
}

_exchanges: dict = {}


def _get_exchange(corretora: str):
    if corretora not in _exchanges:
        cls = getattr(ccxt, corretora)
        cfg = {"enableRateLimit": True, "timeout": 15000, **_CONFIG_CORRETORA.get(corretora, {})}
        _exchanges[corretora] = cls(cfg)
    return _exchanges[corretora]


def reset_exchange_cache() -> None:
    """Uso em testes -- mesma finalidade de `data.fetcher.reset_exchange_cache`."""
    global _exchanges
    _exchanges = {}


def perp_symbol(par_spot: str) -> str:
    """`BTC/USDT` -> `BTC/USDT:USDT` -- formato ccxt para perpetuo linear."""
    base, quote = par_spot.split("/")
    return f"{base}/{quote}:{quote}"


def fetch_funding_rate_history(corretora: str, par_spot: str, dias: int = 90) -> pd.DataFrame:
    """Historico de funding rate (periodo de 8h) do perpetuo correspondente
    ao par spot, numa corretora especifica, paginado ate cobrir `dias`
    ou esgotar o historico disponivel. Devolve DataFrame vazio (nunca
    lanca) quando o par nao tem mercado perpetuo naquela corretora."""
    exchange = _get_exchange(corretora)
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
            log.info(f"{corretora}/{par_spot}: sem mercado perpetuo correspondente ({symbol})")
            return pd.DataFrame(columns=["fundingRate"])
        if not lote:
            break
        registros += lote
        proximo = lote[-1]["timestamp"] + 1
        if proximo <= cursor:
            break
        cursor = proximo
        # NAO assume "lote menor que o limite pedido = fim do historico" --
        # achado real (research.md D1): o cap real por chamada da Gate fica
        # bem abaixo de `_MAX_RECORDS_PER_CALL` e a API trunca em silencio,
        # sem erro. So `while cursor < ate` e lote vazio decidem parar.

    if not registros:
        return pd.DataFrame(columns=["fundingRate"])

    df = pd.DataFrame(registros)
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
    df = df.set_index("timestamp")[["fundingRate"]].sort_index()
    df = df[~df.index.duplicated(keep="last")]
    return df
