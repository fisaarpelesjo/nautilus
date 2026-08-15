import sys

import main


def test_replay_command_is_registered():
    assert "replay" in main.COMMANDS


def test_cmd_replay_runs_replay_and_backtest_and_prints_comparison(monkeypatch):
    import trading.replay as replay_mod
    import backtesting.engine as engine_mod

    monkeypatch.setattr(sys, "argv", ["main.py", "replay", "BTC/USDT"])

    fake_result = replay_mod.ReplayResult(
        symbol="BTC/USDT", timeframe="4h", trades=[{"pnl_usdt": "5.0"}],
        total_trades=1, total_pnl=5.0, blocked_cycles=2,
    )
    calls = {"run_replay": [], "run_backtest": []}
    monkeypatch.setattr(replay_mod, "run_replay", lambda symbol, timeframe=None, candle_limit=300: (
        calls["run_replay"].append((symbol, timeframe, candle_limit)), fake_result,
    )[1])

    from backtesting.engine import BacktestResult
    fake_backtest = BacktestResult(
        trades=[], initial_capital=1000.0, final_capital=1010.0,
        total_return_pct=1.0, win_rate=60.0, total_trades=1,
        max_drawdown_pct=5.0, profit_factor=1.5, expectancy=1.0,
        average_win=2.0, average_loss=-1.0, largest_win=5.0, largest_loss=-2.0,
        max_losing_streak=1, exposure_pct=30.0, sharpe=1.0, expectancy_pct=1.0,
        payoff_ratio=2.0, buy_hold_return_pct=0.5, edge_return_pct=0.5,
        edge_score=2.0, sortino=1.0, calmar=1.0, annualized_return_pct=5.0,
        return_per_exposure_pct=5.0,
    )
    monkeypatch.setattr(engine_mod, "run_backtest", lambda symbol, timeframe, strategy=None, **kwargs: (
        calls["run_backtest"].append((symbol, timeframe)), fake_backtest,
    )[1])

    main.cmd_replay()

    assert len(calls["run_replay"]) == 1
    assert calls["run_replay"][0][0] == "BTC/USDT"
    assert len(calls["run_backtest"]) == 1
