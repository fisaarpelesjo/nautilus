import pandas as pd

from backtesting import mean_reversion_stablecoin as mod


def test_teste_sanidade_zero_trades_sobre_preco_constante():
    assert mod.teste_sanidade() is True


def test_gerar_resultado_custo_zero_remove_fee_e_slippage(monkeypatch):
    capturado = {}

    def _fake_simulate_backtest(df, strategy, fee_rate, slippage_pct):
        capturado["fee_rate"] = fee_rate
        capturado["slippage_pct"] = slippage_pct
        return "resultado-fake"

    monkeypatch.setattr(mod, "simulate_backtest", _fake_simulate_backtest)

    df = mod._candles_preco_constante()

    resultado = mod.gerar_resultado(df, True)

    assert resultado == "resultado-fake"
    assert capturado["fee_rate"] == 0.0
    assert capturado["slippage_pct"] == 0.0

    mod.gerar_resultado(df, False)
    assert capturado["fee_rate"] > 0.0
    assert capturado["slippage_pct"] > 0.0


def test_avaliar_none_quando_fetch_devolve_vazio(monkeypatch):
    monkeypatch.setattr(mod, "fetch_ohlcv", lambda par, tf, limit: pd.DataFrame())

    assert mod.avaliar() is None


def test_avaliar_roda_a_bateria_com_dados_mockados(monkeypatch):
    idx = pd.date_range("2026-01-01", periods=500, freq="4h")
    df = pd.DataFrame({
        "open": 1.0, "high": 1.0005, "low": 0.9995, "close": 1.0, "volume": 1_000_000.0,
    }, index=idx)

    monkeypatch.setattr(mod, "fetch_ohlcv", lambda par, tf, limit: df)

    relatorio = mod.avaliar()

    assert relatorio is not None
    assert relatorio.e1_sanidade_ok is True
    assert relatorio.e2_janela_unica is not None
