"""Historico de long/short ratio e open interest via ccxt (spec 071, H35)."""
import ccxt

from data import long_short_ratio


class _FakeFuturesExchange:
    def __init__(self, ratio_registros=None, oi_registros=None):
        self._ratio = ratio_registros or []
        self._oi = oi_registros or []
        self.calls = []

    def fetch_long_short_ratio_history(self, symbol, timeframe=None, limit=None):
        self.calls.append(("ratio", symbol, timeframe, limit))
        return self._ratio[:limit]

    def fetch_open_interest_history(self, symbol, timeframe=None, limit=None):
        self.calls.append(("oi", symbol, timeframe, limit))
        return self._oi[:limit]


class _BadSymbolExchange:
    def fetch_long_short_ratio_history(self, symbol, timeframe=None, limit=None):
        raise ccxt.BadSymbol(f"binance does not have market symbol {symbol}")

    def fetch_open_interest_history(self, symbol, timeframe=None, limit=None):
        raise ccxt.BadSymbol(f"binance does not have market symbol {symbol}")


def test_par_sem_mercado_perpetuo_devolve_dataframe_vazio_ratio(monkeypatch):
    monkeypatch.setattr(long_short_ratio, "_get_futures_exchange", lambda: _BadSymbolExchange())

    df = long_short_ratio.fetch_long_short_ratio_history("SNDKB/USDT")

    assert len(df) == 0
    assert list(df.columns) == ["longShortRatio"]


def test_par_sem_mercado_perpetuo_devolve_dataframe_vazio_open_interest(monkeypatch):
    monkeypatch.setattr(long_short_ratio, "_get_futures_exchange", lambda: _BadSymbolExchange())

    df = long_short_ratio.fetch_open_interest_history("SNDKB/USDT")

    assert len(df) == 0
    assert list(df.columns) == ["openInterestValue"]


def test_historico_normal_devolve_serie_ordenada_sem_duplicatas(monkeypatch):
    registros = [
        {"timestamp": 1_700_000_000_000, "longShortRatio": 1.05},
        {"timestamp": 1_700_014_400_000, "longShortRatio": 0.90},
        {"timestamp": 1_700_028_800_000, "longShortRatio": 1.10},
    ]
    ex = _FakeFuturesExchange(ratio_registros=registros)
    monkeypatch.setattr(long_short_ratio, "_get_futures_exchange", lambda: ex)

    df = long_short_ratio.fetch_long_short_ratio_history("BTC/USDT", timeframe="4h")

    assert len(df) == 3
    assert df.index.is_monotonic_increasing
    assert not df.index.has_duplicates
    assert list(df["longShortRatio"]) == [1.05, 0.90, 1.10]
    assert ex.calls == [("ratio", "BTC/USDT:USDT", "4h", long_short_ratio._MAX_RECORDS_PER_CALL)]


def test_open_interest_usa_valor_usd_nao_quantidade(monkeypatch):
    registros = [
        {"timestamp": 1_700_000_000_000, "openInterestAmount": 100.0, "openInterestValue": 8_000_000.0},
    ]
    ex = _FakeFuturesExchange(oi_registros=registros)
    monkeypatch.setattr(long_short_ratio, "_get_futures_exchange", lambda: ex)

    df = long_short_ratio.fetch_open_interest_history("BTC/USDT")

    assert list(df.columns) == ["openInterestValue"]
    assert df["openInterestValue"].iloc[0] == 8_000_000.0
