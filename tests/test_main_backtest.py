import sys
from types import SimpleNamespace

import main
import backtesting.compare
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
    from dataclasses import dataclass

    @dataclass
    class _FakeResult:
        total_trades: int = 0

    @dataclass
    class _FakeVerdict:
        status: str = "inconclusivo"

    calls = []
    monkeypatch.setattr(sys, "argv", ["main.py", "backtest", "--validate"])
    monkeypatch.setattr(
        backtesting.validation, "run_backtest_with_validation",
        lambda *a, **k: calls.append(("validate", a, k)) or (_FakeResult(), _FakeResult(), _FakeVerdict()),
    )
    import utils.report_export as report_export_mod
    monkeypatch.setattr(report_export_mod, "export_report", lambda *a, **k: None)

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


def test_compare_command_is_registered_with_pt_br_alias():
    assert "compare" in main.COMMANDS
    assert "comparar" in main.COMMANDS
    assert main.COMMANDS["compare"] is main.COMMANDS["comparar"]


def test_cmd_comparar_calls_backtesting_compare_run(monkeypatch):
    calls = []
    monkeypatch.setattr(backtesting.compare, "run", lambda *a, **k: calls.append((a, k)))

    main.cmd_comparar()

    assert len(calls) == 1


def test_painel_command_is_registered():
    assert "painel" in main.COMMANDS


def test_cmd_painel_calls_trading_panel_print_panel(monkeypatch):
    import trading.panel
    calls = []
    monkeypatch.setattr(trading.panel, "print_panel", lambda manager: calls.append(manager))
    from execution import order_manager
    monkeypatch.setattr(order_manager, "TRADING_MODE", "paper")
    monkeypatch.setattr(order_manager, "load_state", lambda: {})

    main.cmd_painel()

    assert len(calls) == 1


def test_performance_command_is_registered_with_pt_br_alias():
    assert "performance" in main.COMMANDS
    assert "desempenho" in main.COMMANDS
    assert main.COMMANDS["performance"] is main.COMMANDS["desempenho"]


def test_cmd_performance_builds_figures_and_opens_report(monkeypatch, tmp_path):
    from data import trade_store

    monkeypatch.setattr(trade_store, "load_recent_trades", lambda n=100000: [
        {"symbol": "BTC/USDT", "pnl_usdt": "5.0", "closed_at": "2026-01-01", "balance_after": "1005.0"},
    ])
    opened = []
    monkeypatch.setattr("webbrowser.open", lambda url: opened.append(url))
    monkeypatch.setattr(main, "PERFORMANCE_REPORT_PATH", str(tmp_path / "performance.html"))

    main.cmd_performance()

    assert opened[0].startswith("file:///")


def test_cmd_performance_opens_valid_file_uri_from_relative_path(monkeypatch, tmp_path):
    # Regressao (achado de code-review): PERFORMANCE_REPORT_PATH default e
    # relativo ("data/performance_report.html"); f"file://{path}" produzia
    # uma URL malformada (o navegador interpretava "data" como host, nao
    # como parte do caminho) -- o relatorio nunca aparecia de verdade.
    from data import trade_store

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(trade_store, "load_recent_trades", lambda n=100000: [
        {"symbol": "BTC/USDT", "pnl_usdt": "5.0", "closed_at": "2026-01-01", "balance_after": "1005.0"},
    ])
    opened = []
    monkeypatch.setattr("webbrowser.open", lambda url: opened.append(url))
    monkeypatch.setattr(main, "PERFORMANCE_REPORT_PATH", "data/performance_report.html")
    (tmp_path / "data").mkdir()

    main.cmd_performance()

    assert len(opened) == 1
    assert opened[0].startswith("file:///")
    assert "performance_report.html" in opened[0]
    assert (tmp_path / "data" / "performance_report.html").exists()


def test_cmd_backtest_exports_report(monkeypatch):
    from types import SimpleNamespace
    calls = []
    monkeypatch.setattr(sys, "argv", ["main.py", "backtest"])
    fake_result = SimpleNamespace(trades=[])
    monkeypatch.setattr(backtesting.engine, "run_backtest", lambda *a, **k: fake_result)
    import utils.report_export as report_export_mod
    monkeypatch.setattr(report_export_mod, "export_report", lambda name, params, result, ranking=None: calls.append((name, params, result)))

    main.cmd_backtest()

    assert len(calls) == 1
    assert calls[0][0] == "backtest"
    assert calls[0][2] is fake_result


def test_cmd_scan_exports_report(monkeypatch):
    import backtesting.scanner as scanner_mod
    calls = []
    monkeypatch.setattr(scanner_mod, "run_scan", lambda: ["fake_scan_result"])
    monkeypatch.setattr(scanner_mod, "print_scan", lambda results: None)
    import utils.report_export as report_export_mod
    monkeypatch.setattr(report_export_mod, "export_report", lambda name, params, result, ranking=None: calls.append((name, ranking)))

    main.cmd_scan()

    assert len(calls) == 1
    assert calls[0][0] == "scan"
    assert calls[0][1] == ["fake_scan_result"]


def test_cmd_multibacktest_exports_report(monkeypatch):
    import backtesting.multi as multi_mod
    calls = []
    monkeypatch.setattr(multi_mod, "run_all", lambda: ["fake_multi_result"])
    monkeypatch.setattr(multi_mod, "print_results", lambda results: None)
    import utils.report_export as report_export_mod
    monkeypatch.setattr(report_export_mod, "export_report", lambda name, params, result, ranking=None: calls.append((name, ranking)))

    main.cmd_multibacktest()

    assert len(calls) == 1
    assert calls[0][0] == "multibacktest"
    assert calls[0][1] == ["fake_multi_result"]


def test_cmd_backtest_validate_exports_report(monkeypatch):
    # Regressao: cmd_backtest() retornava antes de alcancar export_report() no
    # caminho --validate -- achado de code-review (unico caminho de backtest
    # sem historico auditavel em reports/).
    from dataclasses import dataclass

    @dataclass
    class _FakeBacktestResult:
        total_trades: int

    @dataclass
    class _FakeVerdict:
        status: str

    calls = []
    monkeypatch.setattr(sys, "argv", ["main.py", "backtest", "--validate"])
    fake_train = _FakeBacktestResult(total_trades=5)
    fake_validation = _FakeBacktestResult(total_trades=2)
    fake_verdict = _FakeVerdict(status="aprovado")
    monkeypatch.setattr(
        backtesting.validation, "run_backtest_with_validation",
        lambda *a, **k: (fake_train, fake_validation, fake_verdict),
    )
    import utils.report_export as report_export_mod
    monkeypatch.setattr(report_export_mod, "export_report", lambda name, params, result, ranking=None: calls.append((name, params, result)))

    main.cmd_backtest()

    assert len(calls) == 1
    assert calls[0][0] == "backtest_validate"
    assert calls[0][2]["train"]["total_trades"] == 5
    assert calls[0][2]["validation"]["total_trades"] == 2
    assert calls[0][2]["verdict"]["status"] == "aprovado"


def test_cmd_otimizar_exports_report(monkeypatch):
    import backtesting.optimizer as optimizer_mod
    calls = []
    monkeypatch.setattr(sys, "argv", ["main.py", "optimize"])
    monkeypatch.setattr(optimizer_mod, "_optimize_multi", lambda dfs, validate=False: ["fake_optimize_result"])
    monkeypatch.setattr(optimizer_mod, "_print_results", lambda results, symbols, validate=False: None)
    monkeypatch.setattr(optimizer_mod, "fetch_ohlcv", lambda sym, timeframe, limit=2000: None)
    import utils.report_export as report_export_mod
    monkeypatch.setattr(report_export_mod, "export_report", lambda name, params, result, ranking=None: calls.append((name, ranking)))

    main.cmd_otimizar()

    assert len(calls) == 1
    assert calls[0][0] == "optimize"
    assert calls[0][1] == ["fake_optimize_result"]
