import numpy as np
import pandas as pd

from backtesting.engine import Trade
from backtesting.optimizer import OptimizationParams
from backtesting.robustness import monte_carlo_resample, split_walk_forward_windows, walk_forward_validate
from config.settings import EDGE_MIN_TRADES
from strategy.ema_rsi import EmaRsiParams


def _synthetic_ohlcv_df(n, seed=1):
    rng = np.random.default_rng(seed)
    index = pd.date_range("2026-01-01", periods=n, freq="4h")
    price = 100 + np.cumsum(rng.normal(size=n))
    return pd.DataFrame({
        "open": price, "high": price + np.abs(rng.normal(size=n)),
        "low": price - np.abs(rng.normal(size=n)), "close": price + rng.normal(size=n) * 0.1,
        "volume": rng.random(n) * 100 + 10,
    }, index=index)


def test_split_walk_forward_windows_covers_whole_df_contiguously_unshuffled():
    df = _synthetic_ohlcv_df(900)

    windows = split_walk_forward_windows(df, min_windows=3, min_window_candles=150)

    assert len(windows) == 3
    reconstructed = pd.concat(windows)
    pd.testing.assert_frame_equal(reconstructed, df)
    for a, b in zip(windows, windows[1:], strict=False):
        assert a.index[-1] < b.index[0]


def test_split_walk_forward_windows_returns_empty_when_insufficient_data():
    df = _synthetic_ohlcv_df(300)  # abaixo de 3 * 150

    windows = split_walk_forward_windows(df, min_windows=3, min_window_candles=150)

    assert windows == []


def _default_params():
    return OptimizationParams(strategy=EmaRsiParams(pullback_entry_enabled=False))


def test_walk_forward_validate_reports_status_ok_with_windows_and_summary():
    df = _synthetic_ohlcv_df(900)

    result = walk_forward_validate(df, _default_params(), min_windows=3)

    assert result.status == "ok"
    assert len(result.windows) == 3
    assert result.worst_window is not None
    assert result.worst_window.result.total_return_pct == min(
        w.result.total_return_pct for w in result.windows
    )
    assert result.avg_return_pct == sum(w.result.total_return_pct for w in result.windows) / 3


def test_walk_forward_validate_reports_insufficient_data_status():
    df = _synthetic_ohlcv_df(300)

    result = walk_forward_validate(df, _default_params(), min_windows=3)

    assert result.status == "dados_insuficientes"
    assert result.windows == []


def _trade(pnl):
    now = pd.Timestamp("2026-01-01")
    return Trade(
        entry_price=100.0, exit_price=100.0 + pnl, quantity=1.0, pnl=pnl, pnl_pct=pnl,
        fees=0.0, entry_time=now, exit_time=now, exit_reason="test",
    )


_MIXED_TRADES = [_trade(p) for p in [10, -5, -8, 12, -3, 7, -15, 4, -2, 9, -6, 3]]


def test_monte_carlo_resample_is_deterministic_with_fixed_seed():
    a = monte_carlo_resample(_MIXED_TRADES, n_simulations=200, seed=42)
    b = monte_carlo_resample(_MIXED_TRADES, n_simulations=200, seed=42)

    assert a == b


def test_monte_carlo_resample_produces_coherent_drawdown_percentiles():
    result = monte_carlo_resample(_MIXED_TRADES, n_simulations=500, seed=1)

    assert result.sample_size == len(_MIXED_TRADES)
    assert result.n_simulations == 500
    assert result.max_drawdown_median_pct > 0
    assert result.max_drawdown_p95_pct >= result.max_drawdown_median_pct
    assert 0 <= result.worst_losing_streak_median <= len(_MIXED_TRADES)


def test_monte_carlo_resample_flags_low_confidence_below_edge_min_trades():
    few_trades = _MIXED_TRADES[: EDGE_MIN_TRADES - 1]
    enough_trades = _MIXED_TRADES * 2  # garante >= EDGE_MIN_TRADES

    assert len(enough_trades) >= EDGE_MIN_TRADES
    result_few = monte_carlo_resample(few_trades, n_simulations=50, seed=1)
    result_enough = monte_carlo_resample(enough_trades, n_simulations=50, seed=1)

    assert result_few.low_confidence is True
    assert result_enough.low_confidence is False
