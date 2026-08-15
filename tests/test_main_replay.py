import sys

import pandas as pd

import main


def test_replay_command_is_registered():
    assert "replay" in main.COMMANDS


def _synthetic_ohlcv(n=200):
    closes = [100.0 + (i % 30) * 0.5 - (i // 30) * 0.2 for i in range(n)]
    return pd.DataFrame({
        "open": closes, "high": [c + 1.0 for c in closes], "low": [c - 1.0 for c in closes],
        "close": closes, "volume": [1000.0] * n,
    }, index=pd.date_range("2024-01-01", periods=n, freq="4h"))


def test_cmd_replay_runs_replay_and_backtest_and_prints_comparison(monkeypatch):
    import trading.replay as replay_mod

    monkeypatch.setattr(sys, "argv", ["main.py", "replay", "BTC/USDT"])

    fake_result = replay_mod.ReplayResult(
        symbol="BTC/USDT", timeframe="4h", trades=[{"pnl_usdt": "5.0"}],
        total_trades=1, total_pnl=5.0, blocked_cycles=2,
    )
    calls = {"run_replay": []}
    monkeypatch.setattr(replay_mod, "run_replay", lambda symbol, timeframe=None, candle_limit=300: (
        calls["run_replay"].append((symbol, timeframe, candle_limit)), fake_result,
    )[1])
    monkeypatch.setattr("data.fetcher.fetch_ohlcv", lambda symbol, timeframe, limit=2000: _synthetic_ohlcv())

    main.cmd_replay()

    assert len(calls["run_replay"]) == 1
    assert calls["run_replay"][0][0] == "BTC/USDT"


def test_cmd_replay_does_not_print_full_backtest_report(monkeypatch, capsys):
    # Regressao (achado de code-review): run_backtest() imprime seu proprio
    # relatorio completo internamente (print_report) -- cmd_replay chamava
    # essa funcao direto, poluindo a saida com um bloco de backtest inteiro
    # antes da comparacao concisa pretendida. cmd_replay deve usar
    # simulate_backtest() (nao imprime nada sozinho) em vez de run_backtest().
    import trading.replay as replay_mod
    import backtesting.engine as engine_mod

    monkeypatch.setattr(sys, "argv", ["main.py", "replay", "BTC/USDT"])
    fake_result = replay_mod.ReplayResult(
        symbol="BTC/USDT", timeframe="4h", trades=[], total_trades=0, total_pnl=0.0, blocked_cycles=0,
    )
    monkeypatch.setattr(replay_mod, "run_replay", lambda symbol, timeframe=None, candle_limit=300: fake_result)
    monkeypatch.setattr("data.fetcher.fetch_ohlcv", lambda symbol, timeframe, limit=2000: _synthetic_ohlcv())

    print_report_calls = []
    monkeypatch.setattr(engine_mod, "print_report", lambda result: print_report_calls.append(result))

    main.cmd_replay()

    assert print_report_calls == []


def test_cmd_replay_uses_same_initial_capital_for_backtest_and_comparison(monkeypatch):
    # Regressao (achado de code-review): compare_to_backtest() tinha seu
    # proprio default de initial_capital (1000.0) independente do usado
    # para rodar o backtest -- coincidencia de literais duplicados, nao um
    # vinculo real. Se um dos dois defaults mudasse sozinho no futuro, os
    # dois retornos % comparados deixariam de fazer sentido juntos, em
    # silencio.
    import trading.replay as replay_mod

    monkeypatch.setattr(sys, "argv", ["main.py", "replay", "BTC/USDT"])
    fake_result = replay_mod.ReplayResult(
        symbol="BTC/USDT", timeframe="4h", trades=[], total_trades=0, total_pnl=100.0, blocked_cycles=0,
    )
    monkeypatch.setattr(replay_mod, "run_replay", lambda symbol, timeframe=None, candle_limit=300: fake_result)
    monkeypatch.setattr("data.fetcher.fetch_ohlcv", lambda symbol, timeframe, limit=2000: _synthetic_ohlcv())

    captured = {}
    original_compare = replay_mod.compare_to_backtest

    def _spy_compare(result, backtest_result, initial_capital=1000.0):
        captured["initial_capital_passed_to_compare"] = initial_capital
        captured["backtest_initial_capital"] = backtest_result.initial_capital
        return original_compare(result, backtest_result, initial_capital=initial_capital)

    monkeypatch.setattr(replay_mod, "compare_to_backtest", _spy_compare)

    main.cmd_replay()

    assert captured["initial_capital_passed_to_compare"] == captured["backtest_initial_capital"]
