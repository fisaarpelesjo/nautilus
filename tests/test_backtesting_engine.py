import pandas as pd

from backtesting.engine import simulate_backtest
from strategy.base import Signal, TradeSignal


class SequenceStrategy:
    def __init__(self, signals):
        self.signals = list(signals)

    def generate_signal(self, _df):
        if self.signals:
            return TradeSignal(self.signals.pop(0), 100.0, "test")
        return TradeSignal(Signal.HOLD, 100.0, "test")


def _df(rows):
    index = pd.date_range("2026-01-01", periods=len(rows), freq="h")
    return pd.DataFrame(rows, index=index)


def test_simulate_backtest_applies_fees_and_slippage_on_take_profit():
    data = _df([
        {"open": 100.0, "high": 101.0, "low": 99.0, "close": 100.0, "volume": 1.0},
        {"open": 100.0, "high": 107.0, "low": 99.0, "close": 105.0, "volume": 1.0},
        {"open": 108.0, "high": 112.0, "low": 107.0, "close": 110.0, "volume": 1.0},
    ])
    strategy = SequenceStrategy([Signal.BUY, Signal.HOLD])

    result = simulate_backtest(
        data,
        strategy,
        initial_capital=1000.0,
        start_index=1,
        fee_rate=0.001,
        slippage_pct=0.001,
    )

    assert result.total_trades == 1
    trade = result.trades[0]
    assert trade.exit_reason == "Take Profit"
    assert trade.entry_price > 105.0
    assert trade.exit_price < trade.entry_price * 1.06
    assert trade.fees > 0


def test_simulate_backtest_closes_open_position_at_period_end():
    data = _df([
        {"open": 100.0, "high": 101.0, "low": 99.0, "close": 100.0, "volume": 1.0},
        {"open": 100.0, "high": 101.0, "low": 99.0, "close": 100.0, "volume": 1.0},
        {"open": 102.0, "high": 103.0, "low": 101.0, "close": 102.0, "volume": 1.0},
    ])
    strategy = SequenceStrategy([Signal.BUY, Signal.HOLD])

    result = simulate_backtest(data, strategy, start_index=1, fee_rate=0.0, slippage_pct=0.0)

    assert result.total_trades == 1
    assert result.trades[0].exit_reason == "Fim do periodo"


def test_simulate_backtest_calculates_advanced_metrics():
    data = _df([
        {"open": 100.0, "high": 101.0, "low": 99.0, "close": 100.0, "volume": 1.0},
        {"open": 100.0, "high": 101.0, "low": 99.0, "close": 100.0, "volume": 1.0},
        {"open": 100.0, "high": 101.0, "low": 98.0, "close": 99.0, "volume": 1.0},
        {"open": 100.0, "high": 101.0, "low": 99.0, "close": 100.0, "volume": 1.0},
        {"open": 100.0, "high": 107.0, "low": 99.0, "close": 106.0, "volume": 1.0},
    ])
    strategy = SequenceStrategy([Signal.BUY, Signal.HOLD, Signal.BUY, Signal.HOLD])

    result = simulate_backtest(
        data,
        strategy,
        initial_capital=1000.0,
        start_index=1,
        fee_rate=0.0,
        slippage_pct=0.0,
    )

    assert result.total_trades == 2
    assert result.profit_factor == 4.0
    assert result.expectancy == 2.25
    assert result.average_win == 6.0
    assert result.average_loss == -1.5
    assert result.largest_win == 6.0
    assert result.largest_loss == -1.5
    assert result.max_losing_streak == 1
    assert round(result.exposure_pct, 2) == 66.67
    assert result.sharpe > 0
    assert result.expectancy_pct > 0
    assert result.payoff_ratio == 4.0


def test_simulate_backtest_calculates_buy_hold_and_edge_metrics():
    data = _df([
        {"open": 100.0, "high": 101.0, "low": 99.0, "close": 100.0, "volume": 1.0},
        {"open": 100.0, "high": 101.0, "low": 99.0, "close": 100.0, "volume": 1.0},
        {"open": 120.0, "high": 121.0, "low": 119.0, "close": 120.0, "volume": 1.0},
    ])
    strategy = SequenceStrategy([Signal.HOLD, Signal.HOLD])

    result = simulate_backtest(data, strategy, start_index=1, fee_rate=0.0, slippage_pct=0.0)

    assert result.total_return_pct == 0.0
    assert result.buy_hold_return_pct == 20.0
    assert result.edge_return_pct == -20.0
    assert result.edge_score < 0
