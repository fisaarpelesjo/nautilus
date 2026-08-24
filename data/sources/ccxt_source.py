"""Fonte de dados cripto via ccxt/Binance (spec 023, T008).

ATENCAO: este arquivo e uma EXTRACAO do que estava em data/fetcher.py, sem
alteracao de logica. Cache incremental, singleton de exchange, retry de rate
limit e conversao para DataFrame sao os mesmos.

A extracao foi feita com tests/test_crypto_no_regression.py ja escrito e
passando contra o codigo original -- a abstracao e justamente o tipo de mudanca
que introduz divergencia silenciosa, e este projeto ja perdeu tempo duas vezes
com isso (spec 019, spec 020).

O estado (`_cache`, `_exchange_cache`) permanece em data/fetcher.py em vez de
migrar para ca: e estado global compartilhado, e move-lo mudaria o
comportamento de reset entre testes que a suite ja depende
(`reset_exchange_cache`).
"""
import pandas as pd


class CcxtSource:
    name = "ccxt"

    def fetch_ohlcv(self, symbol: str, timeframe: str, limit: int) -> pd.DataFrame:
        # Delega ao fetcher, que detem o estado de cache e a instancia de
        # exchange. A indirecao existe para que o registro de fontes tenha um
        # objeto uniforme para devolver, sem duplicar a politica de cache.
        from data.fetcher import _fetch_ohlcv_ccxt

        return _fetch_ohlcv_ccxt(symbol, timeframe, limit)
