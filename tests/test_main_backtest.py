import sys

import main
import backtesting.engine
import backtesting.validation


def test_cmd_backtest_runs_plain_backtest_by_default(monkeypatch):
    calls = []
    monkeypatch.setattr(sys, "argv", ["main.py", "backtest"])
    monkeypatch.setattr(backtesting.engine, "run_backtest", lambda *a, **k: calls.append(("plain", a, k)))

    main.cmd_backtest()

    assert calls == [("plain", (main.SYMBOL, main.TIMEFRAME), {})]


def test_cmd_backtest_runs_validation_split_with_flag(monkeypatch):
    calls = []
    monkeypatch.setattr(sys, "argv", ["main.py", "backtest", "--validate"])
    monkeypatch.setattr(backtesting.validation, "run_backtest_with_validation", lambda *a, **k: calls.append(("validate", a, k)))

    main.cmd_backtest()

    assert calls == [("validate", (main.SYMBOL, main.TIMEFRAME), {})]


def test_cmd_edge_runs_edge_report_not_plain_backtest(monkeypatch):
    calls = []
    monkeypatch.setattr(backtesting.validation, "run_edge_report", lambda *a, **k: calls.append(("edge", a, k)))
    monkeypatch.setattr(backtesting.engine, "run_backtest", lambda *a, **k: calls.append(("plain", a, k)))

    main.cmd_edge()

    assert calls == [("edge", (main.SYMBOL, main.TIMEFRAME), {})]
