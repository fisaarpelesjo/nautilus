import pandas as pd

from strategy.base import Signal


def _synthetic_ohlcv(n=250, seed_high=100.0):
    closes = [seed_high] * n
    return pd.DataFrame({
        "open":   closes,
        "high":   [c + 1.0 for c in closes],
        "low":    [c - 1.0 for c in closes],
        "close":  closes,
        "volume": [1000.0] * n,
    }, index=pd.date_range("2024-01-01", periods=n, freq="4h"))


def test_calculate_indicators_uses_shift_to_avoid_lookahead():
    from strategy.breakout import BreakoutStrategy

    strategy = BreakoutStrategy(window=10)
    df = _synthetic_ohlcv(n=30)
    # ultimo candle tem uma maxima muito alta -- shift(1) garante que
    # breakout_high do PROPRIO candle nao inclua essa maxima.
    df.loc[df.index[-1], "high"] = 1000.0

    result = strategy.calculate_indicators(df)

    assert "breakout_high" in result.columns
    assert "breakout_low" in result.columns
    last_breakout_high = result.iloc[-1]["breakout_high"]
    assert last_breakout_high < 1000.0


def test_generate_signal_returns_buy_on_breakout_above_window_high():
    from strategy.breakout import BreakoutStrategy

    strategy = BreakoutStrategy(window=10)
    df = _synthetic_ohlcv(n=30, seed_high=100.0)
    # ultimo candle rompe muito acima da faixa 99-101 dos anteriores.
    df.loc[df.index[-1], "close"] = 150.0
    df.loc[df.index[-1], "high"] = 151.0

    signal = strategy.generate_signal(df)

    assert signal.signal == Signal.BUY


def test_generate_signal_returns_sell_on_breakdown_below_window_low():
    from strategy.breakout import BreakoutStrategy

    strategy = BreakoutStrategy(window=10)
    df = _synthetic_ohlcv(n=30, seed_high=100.0)
    df.loc[df.index[-1], "close"] = 50.0
    df.loc[df.index[-1], "low"] = 49.0

    signal = strategy.generate_signal(df)

    assert signal.signal == Signal.SELL


def test_generate_signal_returns_hold_within_range():
    from strategy.breakout import BreakoutStrategy

    strategy = BreakoutStrategy(window=10)
    df = _synthetic_ohlcv(n=30, seed_high=100.0)

    signal = strategy.generate_signal(df)

    assert signal.signal == Signal.HOLD


def test_generate_signal_returns_hold_with_explicit_reason_when_data_insufficient():
    from strategy.breakout import BreakoutStrategy

    strategy = BreakoutStrategy(window=50)
    df = _synthetic_ohlcv(n=10)  # menos que a janela de 50

    signal = strategy.generate_signal(df)

    assert signal.signal == Signal.HOLD
    assert signal.reason


def test_calculate_indicators_includes_atr_for_risk_manager_compatibility():
    from strategy.breakout import BreakoutStrategy

    strategy = BreakoutStrategy(window=10)
    df = _synthetic_ohlcv(n=30)

    result = strategy.calculate_indicators(df)

    assert "atr" in result.columns
