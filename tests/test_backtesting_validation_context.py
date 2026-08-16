import pandas as pd

from backtesting import validation


def _synthetic_ohlcv(n=200):
    closes = [100.0 + i * 0.1 for i in range(n)]
    return pd.DataFrame({
        "open": closes, "high": [c + 1.0 for c in closes], "low": [c - 1.0 for c in closes],
        "close": closes, "volume": [1000.0] * n,
    }, index=pd.date_range("2024-01-01", periods=n, freq="4h"))


def test_run_edge_report_shows_simulation_context_before_report(monkeypatch):
    df = _synthetic_ohlcv()
    monkeypatch.setattr(validation, "fetch_ohlcv", lambda symbol, timeframe, limit=2000: df)
    monkeypatch.setattr(validation, "print_report", lambda result: None)

    calls = []
    monkeypatch.setattr(
        validation, "simulation_context_banner",
        lambda symbol, timeframe, period_start, period_end, initial_capital: calls.append(
            (symbol, timeframe, period_start, period_end, initial_capital)
        ),
    )

    validation.run_edge_report("BTC/USDT", "4h", initial_capital=500.0)

    assert len(calls) == 1
    symbol, timeframe, period_start, period_end, initial_capital = calls[0]
    assert symbol == "BTC/USDT"
    assert timeframe == "4h"
    assert period_start == df.index[0]
    assert period_end == df.index[-1]
    assert initial_capital == 500.0


def test_run_edge_report_with_validate_also_shows_simulation_context(monkeypatch):
    # Achado de /code-review medium: `edge --validate` delegava direto para
    # run_backtest_with_validation() e nunca mostrava o banner de contexto,
    # ao contrario do caminho default -- inconsistente entre os dois modos do
    # mesmo comando.
    df = _synthetic_ohlcv(n=600)
    monkeypatch.setattr(validation, "fetch_ohlcv", lambda symbol, timeframe, limit=2000: df)
    monkeypatch.setattr(validation, "print_report", lambda result: None)

    calls = []
    monkeypatch.setattr(
        validation, "simulation_context_banner",
        lambda symbol, timeframe, period_start, period_end, initial_capital: calls.append(
            (symbol, timeframe, period_start, period_end, initial_capital)
        ),
    )

    validation.run_edge_report("BTC/USDT", "4h", initial_capital=500.0, validate=True)

    assert len(calls) == 1
    assert calls[0][:2] == ("BTC/USDT", "4h")
    assert calls[0][4] == 500.0


def test_run_edge_report_with_validate_shows_diagnosis_when_reprovado(monkeypatch):
    # Achado de /code-review medium: `edge --validate` nunca passava a
    # diagnose_profile() para _print_verdict, diferente do caminho default.
    from backtesting.approval import ApprovalVerdict

    df = _synthetic_ohlcv(n=600)
    monkeypatch.setattr(validation, "fetch_ohlcv", lambda symbol, timeframe, limit=2000: df)
    monkeypatch.setattr(validation, "print_report", lambda result: None)
    monkeypatch.setattr(validation, "simulation_context_banner", lambda *a, **k: None)

    fake_train = object()
    fake_validation = object()
    fake_verdict = ApprovalVerdict(status="reprovado", reasons=["motivo qualquer"])
    monkeypatch.setattr(
        validation, "run_backtest_with_validation",
        lambda *a, **k: (fake_train, fake_validation, fake_verdict),
    )

    printed = []
    monkeypatch.setattr(validation, "diagnose_profile", lambda result: "perfil agressivo: fake")
    monkeypatch.setattr(validation.console, "print", lambda msg="": printed.append(msg))

    validation.run_edge_report("BTC/USDT", "4h", validate=True)

    assert any("perfil agressivo" in str(msg) for msg in printed)
