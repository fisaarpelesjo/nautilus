from backtesting import compare
from strategy.base import Signal, TradeSignal


class _FakeStrategy:
    def __init__(self, name):
        self.name = name

    def calculate_indicators(self, df):
        return df

    def generate_signal(self, df):
        return TradeSignal(Signal.HOLD, 100.0, "fake")


def _fake_run_backtest(pair, timeframe, strategy=None, **kwargs):
    from backtesting.engine import BacktestResult

    return BacktestResult(
        trades=[], initial_capital=1000.0, final_capital=1150.0,
        total_return_pct=15.0, win_rate=60.0, total_trades=10,
        max_drawdown_pct=8.0, profit_factor=1.5, expectancy=1.0,
        average_win=2.0, average_loss=-1.0, largest_win=5.0, largest_loss=-2.0,
        max_losing_streak=2, exposure_pct=40.0, sharpe=1.2, expectancy_pct=1.0,
        payoff_ratio=2.0, buy_hold_return_pct=5.0, edge_return_pct=10.0,
        edge_score=10.0, sortino=1.5, calmar=1.8,
        annualized_return_pct=20.0, return_per_exposure_pct=25.0,
    )


def test_run_comparison_returns_one_row_per_strategy_and_pair(monkeypatch):
    monkeypatch.setattr(compare, "run_backtest", _fake_run_backtest)
    strategies = {"EMA/RSI": _FakeStrategy("ema"), "Breakout 150": _FakeStrategy("breakout")}

    results = compare.run_comparison(strategies, pairs=["BTC/USDT", "ETH/USDT"], timeframe="4h")

    assert len(results) == 4  # 2 estrategias x 2 pares
    names = {r.strategy_name for r in results}
    assert names == {"EMA/RSI", "Breakout 150"}
    assert all(r.verdict is not None for r in results)


def test_run_comparison_works_with_single_strategy(monkeypatch):
    # Edge Case do spec.md: nao exige minimo de itens para comparar.
    monkeypatch.setattr(compare, "run_backtest", _fake_run_backtest)
    strategies = {"EMA/RSI": _FakeStrategy("ema")}

    results = compare.run_comparison(strategies, pairs=["BTC/USDT"], timeframe="4h")

    assert len(results) == 1
    assert results[0].strategy_name == "EMA/RSI"


def test_run_comparison_uses_evaluate_approval_for_verdict(monkeypatch):
    from backtesting.approval import ApprovalVerdict

    monkeypatch.setattr(compare, "run_backtest", _fake_run_backtest)
    captured = []

    def _spy_evaluate_approval(result, **kwargs):
        captured.append(result)
        return ApprovalVerdict(status="aprovado", reasons=[])

    monkeypatch.setattr(compare, "evaluate_approval", _spy_evaluate_approval)
    strategies = {"EMA/RSI": _FakeStrategy("ema")}

    results = compare.run_comparison(strategies, pairs=["BTC/USDT"], timeframe="4h")

    assert len(captured) == 1
    assert results[0].verdict.status == "aprovado"
