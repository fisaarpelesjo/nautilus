import numpy as np
import pandas as pd

from backtesting.engine import precompute_signals, simulate_backtest
from backtesting.optimizer import _optimize_multi
from backtesting.validation import split_train_validation
from strategy.ema_rsi import EmaRsiStrategy


def _synthetic_ohlcv_df(n, seed=1):
    rng = np.random.default_rng(seed)
    index = pd.date_range("2026-01-01", periods=n, freq="4h")
    price = 100 + np.cumsum(rng.normal(size=n))
    return pd.DataFrame({
        "open": price, "high": price + np.abs(rng.normal(size=n)),
        "low": price - np.abs(rng.normal(size=n)), "close": price + rng.normal(size=n) * 0.1,
        "volume": rng.random(n) * 100 + 10,
    }, index=index)


_SINGLE_COMBO_GRID = {
    "ema_fast": [9],
    "ema_slow": [21],
    "rsi_overbought": [70],
    "volume_min_ratio": [1.0],
    "bb_std": [2.0],
    "atr_sl_multiplier": [1.5],
    "atr_tp_multiplier": [3.0],
}


def _expected_result(df, params, df_slice, start_index=100):
    strategy = EmaRsiStrategy(params.strategy)
    prepared = strategy.calculate_indicators(df.copy())
    signals = precompute_signals(prepared, strategy)
    return simulate_backtest(
        df_slice, strategy,
        atr_sl_multiplier=params.atr_sl_multiplier,
        atr_tp_multiplier=params.atr_tp_multiplier,
        stop_loss_pct=params.stop_loss_pct,
        take_profit_pct=params.take_profit_pct,
        start_index=start_index,
        precomputed_signals=signals.loc[df_slice.index],
    )


def test_optimize_multi_with_validate_scores_using_only_train_slice():
    df = _synthetic_ohlcv_df(600)
    dfs = {"FAKE/USDT": df}

    results = _optimize_multi(dfs, grid=_SINGLE_COMBO_GRID, top_n=1, min_trades_per_pair=0, validate=True)

    assert len(results) == 1
    item = results[0]

    strategy = EmaRsiStrategy(item.params.strategy)
    prepared = strategy.calculate_indicators(df.copy())
    train_df, validation_df = split_train_validation(prepared)
    assert validation_df is not None  # garante que o teste exercita o caso com validacao

    expected_train = _expected_result(df, item.params, train_df, start_index=100)

    assert item.avg_return == expected_train.total_return_pct
    assert item.total_trades == expected_train.total_trades


def test_optimize_multi_with_validate_reports_validation_metrics():
    df = _synthetic_ohlcv_df(600)
    dfs = {"FAKE/USDT": df}

    results = _optimize_multi(dfs, grid=_SINGLE_COMBO_GRID, top_n=1, min_trades_per_pair=0, validate=True)
    item = results[0]

    strategy = EmaRsiStrategy(item.params.strategy)
    prepared = strategy.calculate_indicators(df.copy())
    _train_df, validation_df = split_train_validation(prepared)

    expected_validation = _expected_result(df, item.params, validation_df, start_index=0)

    assert item.validation_avg_return == expected_validation.total_return_pct
    assert item.validation_avg_drawdown == expected_validation.max_drawdown_pct
    assert item.validation_total_trades == expected_validation.total_trades
    assert item.validation_symbols_skipped == []


def test_optimize_multi_with_validate_skips_symbol_without_enough_data():
    long_df = _synthetic_ohlcv_df(600, seed=1)
    short_df = _synthetic_ohlcv_df(200, seed=2)  # abaixo do minimo para as duas fatias
    dfs = {"LONG/USDT": long_df, "SHORT/USDT": short_df}

    results = _optimize_multi(dfs, grid=_SINGLE_COMBO_GRID, top_n=1, min_trades_per_pair=0, validate=True)
    item = results[0]

    assert "SHORT/USDT" in item.validation_symbols_skipped
    assert "LONG/USDT" not in item.validation_symbols_skipped


def test_optimize_multi_without_validate_leaves_validation_fields_at_default():
    df = _synthetic_ohlcv_df(600)
    dfs = {"FAKE/USDT": df}

    results = _optimize_multi(dfs, grid=_SINGLE_COMBO_GRID, top_n=1, min_trades_per_pair=0, validate=False)
    item = results[0]

    assert item.validation_avg_return is None
    assert item.validation_avg_drawdown is None
    assert item.validation_total_trades == 0
    assert item.validation_symbols_skipped == []
