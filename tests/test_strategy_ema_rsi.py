import pandas as pd

from strategy.base import Signal
from strategy.ema_rsi import EmaRsiStrategy


def _strategy_with_indicators(monkeypatch, rows):
    strategy = EmaRsiStrategy()
    df = pd.DataFrame(rows)
    monkeypatch.setattr(strategy, "calculate_indicators", lambda _df: df)
    return strategy


def test_generate_signal_returns_buy_when_entry_filters_pass(monkeypatch):
    strategy = _strategy_with_indicators(
        monkeypatch,
        [
            {
                "close": 100.0,
                "ema_fast": 9.0,
                "ema_slow": 10.0,
                "ema_trend": 90.0,
                "rsi": 50.0,
                "volume": 150.0,
                "volume_ma": 100.0,
                "bb_upper": 120.0,
            },
            {
                "close": 110.0,
                "ema_fast": 12.0,
                "ema_slow": 10.0,
                "ema_trend": 95.0,
                "rsi": 55.0,
                "volume": 150.0,
                "volume_ma": 100.0,
                "bb_upper": 120.0,
            },
        ],
    )

    signal = strategy.generate_signal(pd.DataFrame())

    assert signal.signal == Signal.BUY
    assert signal.price == 110.0


def test_generate_signal_returns_sell_on_bearish_cross(monkeypatch):
    strategy = _strategy_with_indicators(
        monkeypatch,
        [
            {
                "close": 110.0,
                "ema_fast": 12.0,
                "ema_slow": 10.0,
                "ema_trend": 90.0,
                "rsi": 50.0,
                "volume": 150.0,
                "volume_ma": 100.0,
                "bb_upper": 120.0,
            },
            {
                "close": 100.0,
                "ema_fast": 9.0,
                "ema_slow": 10.0,
                "ema_trend": 90.0,
                "rsi": 45.0,
                "volume": 150.0,
                "volume_ma": 100.0,
                "bb_upper": 120.0,
            },
        ],
    )

    signal = strategy.generate_signal(pd.DataFrame())

    assert signal.signal == Signal.SELL
    assert signal.price == 100.0


def test_generate_signal_returns_buy_on_pullback_in_uptrend(monkeypatch):
    strategy = _strategy_with_indicators(
        monkeypatch,
        [
            {
                "open": 105.0,
                "high": 111.0,
                "low": 104.0,
                "close": 108.0,
                "ema_fast": 107.0,
                "ema_slow": 102.0,
                "ema_trend": 95.0,
                "rsi": 55.0,
                "volume": 100.0,
                "volume_ma": 100.0,
                "bb_upper": 120.0,
            },
            {
                "open": 105.0,
                "high": 112.0,
                "low": 102.5,
                "close": 110.0,
                "ema_fast": 108.0,
                "ema_slow": 103.0,
                "ema_trend": 96.0,
                "rsi": 58.0,
                "volume": 150.0,
                "volume_ma": 100.0,
                "bb_upper": 120.0,
            },
        ],
    )

    signal = strategy.generate_signal(pd.DataFrame())

    assert signal.signal == Signal.BUY
    assert "Pullback" in signal.reason
