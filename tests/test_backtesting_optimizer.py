from backtesting.engine import BacktestResult
from backtesting.optimizer import _iter_param_sets, _score_result


def _result(total_return, drawdown, trades=3, win_rate=50, profit_factor=1.5, losing_streak=1):
    return BacktestResult(
        trades=[],
        initial_capital=1000.0,
        final_capital=1000.0 + total_return,
        total_return_pct=total_return,
        win_rate=win_rate,
        total_trades=trades,
        max_drawdown_pct=drawdown,
        profit_factor=profit_factor,
        expectancy=0.0,
        average_win=0.0,
        average_loss=0.0,
        largest_win=0.0,
        largest_loss=0.0,
        max_losing_streak=losing_streak,
        exposure_pct=0.0,
        sharpe=0.0,
    )


def test_iter_param_sets_skips_invalid_ema_combinations():
    grid = {
        "ema_fast": [9, 21],
        "ema_slow": [21],
        "rsi_overbought": [65],
        "volume_min_ratio": [1.2],
        "bb_std": [2.0],
        "atr_sl_multiplier": [1.5],
        "atr_tp_multiplier": [3.0],
    }

    params = list(_iter_param_sets(grid))

    assert len(params) == 1
    assert params[0].strategy.ema_fast == 9
    assert params[0].strategy.ema_slow == 21


def test_score_penalizes_low_trade_count():
    assert _score_result(_result(total_return=50, drawdown=0, trades=1), min_trades=2) == -9999.0


def test_score_prefers_better_return_with_lower_drawdown():
    strong = _score_result(_result(total_return=10, drawdown=2), min_trades=2)
    weak = _score_result(_result(total_return=4, drawdown=8), min_trades=2)

    assert strong > weak
