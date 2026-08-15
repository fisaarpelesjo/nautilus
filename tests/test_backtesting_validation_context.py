import pandas as pd

from backtesting import validation


def _synthetic_ohlcv(n=200):
    closes = [100.0 + i * 0.1 for i in range(n)]
    return pd.DataFrame({
        "open": closes, "high": [c + 1.0 for c in closes], "low": [c - 1.0 for c in closes],
        "close": closes, "volume": [1000.0] * n,
    }, index=pd.date_range("2024-01-01", periods=n, freq="4h"))


def test_run_edge_report_shows_simulation_context_before_report(monkeypatch):
    df = _synthetic_ohlcv()
    monkeypatch.setattr(validation, "fetch_ohlcv", lambda symbol, timeframe, limit=2000: df)
    monkeypatch.setattr(validation, "print_report", lambda result: None)

    calls = []
    monkeypatch.setattr(
        validation, "simulation_context_banner",
        lambda symbol, timeframe, period_start, period_end, initial_capital: calls.append(
            (symbol, timeframe, period_start, period_end, initial_capital)
        ),
    )

    validation.run_edge_report("BTC/USDT", "4h", initial_capital=500.0)

    assert len(calls) == 1
    symbol, timeframe, period_start, period_end, initial_capital = calls[0]
    assert symbol == "BTC/USDT"
    assert timeframe == "4h"
    assert period_start == df.index[0]
    assert period_end == df.index[-1]
    assert initial_capital == 500.0
