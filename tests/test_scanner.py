import backtesting.scanner as scanner
from backtesting.engine import BacktestResult


def _result(edge_score, profit_factor=1.5, total_trades=15, total_return_pct=20.0,
            buy_hold_return_pct=5.0, max_drawdown_pct=5.0, win_rate=50.0, final_capital=1100.0):
    return BacktestResult(
        trades=[],
        initial_capital=1000.0,
        final_capital=final_capital,
        total_return_pct=total_return_pct,
        win_rate=win_rate,
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
        edge_score=edge_score,
    )


def test_run_scan_populates_verdict_and_edge_score(monkeypatch):
    monkeypatch.setattr(scanner, "get_top_pairs", lambda: ["FAKE/USDT"])
    monkeypatch.setattr(scanner, "run_backtest", lambda pair, tf, candle_limit: _result(edge_score=12.3))
    monkeypatch.setattr(scanner, "_get_volume", lambda pair: 50_000_000.0)

    results = scanner.run_scan()

    assert len(results) == 1
    r = results[0]
    assert r.profit_factor == 1.5
    assert r.buy_hold_return_pct == 5.0
    assert r.edge_score == 12.3
    assert r.verdict is not None
    assert r.verdict.status == "aprovado"
    assert r.error is None


def test_run_scan_orders_by_edge_score_descending(monkeypatch):
    monkeypatch.setattr(scanner, "get_top_pairs", lambda: ["A/USDT", "B/USDT", "C/USDT"])
    scores = {"A/USDT": 5.0, "B/USDT": 20.0, "C/USDT": -3.0}
    monkeypatch.setattr(scanner, "run_backtest",
                         lambda pair, tf, candle_limit: _result(edge_score=scores[pair]))
    monkeypatch.setattr(scanner, "_get_volume", lambda pair: 50_000_000.0)

    results = scanner.run_scan()

    assert [r.pair for r in results] == ["B/USDT", "A/USDT", "C/USDT"]


def test_run_scan_marks_failed_pair_as_error_entry_without_dropping_others(monkeypatch):
    monkeypatch.setattr(scanner, "get_top_pairs", lambda: ["GOOD/USDT", "BAD/USDT"])

    def fake_run_backtest(pair, tf, candle_limit):
        if pair == "BAD/USDT":
            raise RuntimeError("symbol invalido")
        return _result(edge_score=1.0)

    monkeypatch.setattr(scanner, "run_backtest", fake_run_backtest)
    monkeypatch.setattr(scanner, "_get_volume", lambda pair: 50_000_000.0)

    results = scanner.run_scan()

    assert len(results) == 2
    bad = next(r for r in results if r.pair == "BAD/USDT")
    good = next(r for r in results if r.pair == "GOOD/USDT")
    assert bad.error == "symbol invalido"
    assert bad.verdict is None
    assert good.error is None
