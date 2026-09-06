"""Historico de long/short ratio (posicionamento) e open interest de
perpetuos USDT-M na Binance -- fonte de dados para H35
(specs/071-h35-crowding-long-short/). Mesma exchange futures de
data/funding.py (defaultType=future), via os metodos unificados ccxt
`fetch_long_short_ratio_history`/`fetch_open_interest_history`.

Retencao medida empiricamente em 2026-09-06 (ver
specs/071-h35-crowding-long-short/research.md D6): ambos os endpoints
devolvem so ~31 dias de historico (186 candles de 4h), independente do
timeframe pedido ou do par -- limite do proprio endpoint publico de
"estatisticas de mercado" da Binance, nao do parametro `limit`. Muito
menor que a retencao completa de funding rate (`data/funding.py`).
"""
import ccxt
import pandas as pd

from data.fetcher import _call_with_rate_limit_retry
from data.funding import _get_futures_exchange, perp_symbol
from utils.logger import get_logger

log = get_logger("long_short_ratio")

# Limite nativo do endpoint (diferente do de candles/funding, que aceitam 1000).
_MAX_RECORDS_PER_CALL = 500


def _fetch_history(metodo, par_spot: str, timeframe: str, coluna: str) -> pd.DataFrame:
    """`coluna` e o campo relevante do registro ccxt (`longShortRatio` ou
    `openInterestValue`). DataFrame vazio (nunca lanca) quando o par nao tem
    mercado perpetuo correspondente -- mesma politica de
    `data/funding.py::fetch_funding_rate_history`."""
    symbol = perp_symbol(par_spot)
    try:
        registros = _call_with_rate_limit_retry(
            metodo, symbol, timeframe=timeframe, limit=_MAX_RECORDS_PER_CALL,
        )
    except ccxt.BadSymbol:
        log.info(f"{par_spot}: sem mercado perpetuo correspondente ({symbol})")
        return pd.DataFrame(columns=[coluna])
    if not registros:
        return pd.DataFrame(columns=[coluna])

    df = pd.DataFrame(registros)
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
    df = df.set_index("timestamp")[[coluna]].sort_index()
    return df[~df.index.duplicated(keep="last")]


def fetch_long_short_ratio_history(par_spot: str, timeframe: str = "4h") -> pd.DataFrame:
    """Coluna `longShortRatio`: razao contas compradas/vendidas (posicionamento
    bruto), nao custo de manter a posicao (isso e `data/funding.py`)."""
    exchange = _get_futures_exchange()
    return _fetch_history(exchange.fetch_long_short_ratio_history, par_spot, timeframe, "longShortRatio")


def fetch_open_interest_history(par_spot: str, timeframe: str = "4h") -> pd.DataFrame:
    """Coluna `openInterestValue`: capital comprometido em USD (nocional) --
    nao `openInterestAmount` (unidades do ativo base), que nao e comparavel
    entre pares de preco muito diferente."""
    exchange = _get_futures_exchange()
    return _fetch_history(exchange.fetch_open_interest_history, par_spot, timeframe, "openInterestValue")
