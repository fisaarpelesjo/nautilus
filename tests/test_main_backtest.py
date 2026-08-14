import sys
from types import SimpleNamespace

import main
import backtesting.engine
import backtesting.optimizer
import backtesting.robustness
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


def test_cmd_otimizar_runs_plain_by_default(monkeypatch):
    calls = []
    monkeypatch.setattr(sys, "argv", ["main.py", "optimize"])
    monkeypatch.setattr(backtesting.optimizer, "run", lambda *a, **k: calls.append((a, k)))

    main.cmd_otimizar()

    assert calls == [((), {"validate": False, "walk_forward": False})]


def test_cmd_otimizar_runs_with_validate_flag(monkeypatch):
    calls = []
    monkeypatch.setattr(sys, "argv", ["main.py", "optimize", "--validate"])
    monkeypatch.setattr(backtesting.optimizer, "run", lambda *a, **k: calls.append((a, k)))

    main.cmd_otimizar()

    assert calls == [((), {"validate": True, "walk_forward": False})]


def test_cmd_otimizar_runs_with_walk_forward_flag(monkeypatch):
    calls = []
    monkeypatch.setattr(sys, "argv", ["main.py", "optimize", "--walk-forward"])
    monkeypatch.setattr(backtesting.optimizer, "run", lambda *a, **k: calls.append((a, k)))

    main.cmd_otimizar()

    assert calls == [((), {"validate": True, "walk_forward": True})]


def test_cmd_backtest_runs_montecarlo_report_with_flag(monkeypatch):
    calls = []
    fake_result = SimpleNamespace(trades=["t1", "t2"])
    monkeypatch.setattr(sys, "argv", ["main.py", "backtest", "--montecarlo"])
    monkeypatch.setattr(backtesting.engine, "run_backtest", lambda *a, **k: fake_result)
    monkeypatch.setattr(backtesting.robustness, "run_monte_carlo_report", lambda trades: calls.append(trades))

    main.cmd_backtest()

    assert calls == [fake_result.trades]


def test_cmd_backtest_without_montecarlo_flag_does_not_run_report(monkeypatch):
    calls = []
    fake_result = SimpleNamespace(trades=["t1"])
    monkeypatch.setattr(sys, "argv", ["main.py", "backtest"])
    monkeypatch.setattr(backtesting.engine, "run_backtest", lambda *a, **k: fake_result)
    monkeypatch.setattr(backtesting.robustness, "run_monte_carlo_report", lambda trades: calls.append(trades))

    main.cmd_backtest()

    assert calls == []
