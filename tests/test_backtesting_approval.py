from backtesting.approval import evaluate_approval
from backtesting.engine import BacktestResult


def _result(total_trades, total_return_pct, buy_hold_return_pct, profit_factor, max_drawdown_pct):
    return BacktestResult(
        trades=[],
        initial_capital=1000.0,
        final_capital=1000.0 * (1 + total_return_pct / 100),
        total_return_pct=total_return_pct,
        win_rate=0.0,
        total_trades=total_trades,
        max_drawdown_pct=max_drawdown_pct,
        profit_factor=profit_factor,
        expectancy=0.0,
        average_win=0.0,
        average_loss=0.0,
        largest_win=0.0,
        largest_loss=0.0,
        max_losing_streak=0,
        exposure_pct=0.0,
        sharpe=0.0,
        expectancy_pct=0.0,
        payoff_ratio=0.0,
        buy_hold_return_pct=buy_hold_return_pct,
        edge_return_pct=total_return_pct - buy_hold_return_pct,
        edge_score=0.0,
    )


def test_evaluate_approval_approves_when_all_criteria_pass():
    result = _result(total_trades=15, total_return_pct=20.0, buy_hold_return_pct=5.0,
                      profit_factor=1.5, max_drawdown_pct=8.0)

    verdict = evaluate_approval(result)

    assert verdict.status == "aprovado"
    assert verdict.reasons == []


def test_evaluate_approval_rejects_when_profit_factor_below_minimum():
    result = _result(total_trades=15, total_return_pct=20.0, buy_hold_return_pct=5.0,
                      profit_factor=1.1, max_drawdown_pct=8.0)

    verdict = evaluate_approval(result)

    assert verdict.status == "reprovado"
    assert any("profit factor" in r for r in verdict.reasons)


def test_evaluate_approval_rejects_when_return_does_not_beat_buy_and_hold():
    result = _result(total_trades=15, total_return_pct=4.0, buy_hold_return_pct=5.0,
                      profit_factor=1.5, max_drawdown_pct=8.0)

    verdict = evaluate_approval(result)

    assert verdict.status == "reprovado"
    assert any("buy-and-hold" in r for r in verdict.reasons)


def test_evaluate_approval_rejects_when_drawdown_too_high():
    result = _result(total_trades=15, total_return_pct=20.0, buy_hold_return_pct=5.0,
                      profit_factor=1.5, max_drawdown_pct=15.0)

    verdict = evaluate_approval(result)

    assert verdict.status == "reprovado"
    assert any("drawdown" in r for r in verdict.reasons)


def test_evaluate_approval_rejects_when_too_few_trades():
    result = _result(total_trades=3, total_return_pct=20.0, buy_hold_return_pct=5.0,
                      profit_factor=1.5, max_drawdown_pct=8.0)

    verdict = evaluate_approval(result)

    assert verdict.status == "reprovado"
    assert any("trades" in r for r in verdict.reasons)


def test_evaluate_approval_is_inconclusive_when_result_missing():
    verdict = evaluate_approval(None)

    assert verdict.status == "inconclusivo"
    assert verdict.reasons
