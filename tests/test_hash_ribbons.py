import pandas as pd
import pytest

from backtesting import hash_ribbons as mod
from strategy.base import Signal
from strategy.hash_ribbons import HashRibbonsStrategy, _alinhar_causal, precompute_signals


def _serie_com_cruzamento_de_alta_e_baixa(n=140):
    """Plana (capitulacao) -> rampa de alta (recuperacao, forca ma30 > ma60)
    -> rampa de queda (forca ma30 < ma60 de novo) -> plana. Indice tz-aware
    (UTC), mesmo formato real de `data.onchain.fetch_onchain_series`."""
    idx = pd.date_range("2026-01-01", periods=n, freq="D", tz="UTC")
    valores = (
        [100.0] * 60
        + [100.0 + 10 * i for i in range(1, 21)]
        + [300.0 - 10 * i for i in range(1, 21)]
        + [100.0] * (n - 100)
    )
    return pd.Series(valores[:n], index=idx)


def _candles_diarios_ate(dia_final: pd.Timestamp, inicio: pd.Timestamp) -> pd.DataFrame:
    """Indice tz-naive, mesmo formato real de `data.fetcher.fetch_ohlcv`."""
    idx = pd.date_range(inicio.tz_localize(None), (dia_final + pd.Timedelta(hours=20)).tz_localize(None), freq="4h")
    return pd.DataFrame({
        "open": 1.0, "high": 1.01, "low": 0.99, "close": 1.0, "volume": 1000.0,
    }, index=idx)


def test_alinhar_causal_nunca_ve_o_dia_do_proprio_candle():
    dias = pd.date_range("2026-01-01", periods=3, freq="D", tz="UTC")
    serie_diaria = pd.Series([10.0, 20.0, 30.0], index=dias)

    candle_meio_dia = pd.DatetimeIndex(["2026-01-02 12:00:00"])  # tz-naive, como fetch_ohlcv
    resultado = _alinhar_causal(candle_meio_dia, serie_diaria)

    assert resultado.iloc[0] == pytest.approx(10.0)


def test_cruzamento_de_alta_gera_buy_no_candle_do_dia_seguinte():
    hashrate = _serie_com_cruzamento_de_alta_e_baixa()
    strategy = HashRibbonsStrategy(hashrate)
    cruzamentos = strategy._cruzamentos_diarios()
    dias_alta = cruzamentos.index[cruzamentos["cruzamento_alta"]]
    assert len(dias_alta) >= 1
    dia_cruzamento = dias_alta[0]
    candle_dia = dia_cruzamento + pd.Timedelta(days=1)

    candles = _candles_diarios_ate(candle_dia, hashrate.index[0])
    sinal = strategy.generate_signal(candles)

    assert sinal.signal == Signal.BUY


def test_cruzamento_de_baixa_gera_sell_no_candle_do_dia_seguinte():
    hashrate = _serie_com_cruzamento_de_alta_e_baixa()
    strategy = HashRibbonsStrategy(hashrate)
    cruzamentos = strategy._cruzamentos_diarios()
    dias_baixa = cruzamentos.index[cruzamentos["cruzamento_baixa"]]
    assert len(dias_baixa) >= 1
    dia_cruzamento = dias_baixa[0]
    candle_dia = dia_cruzamento + pd.Timedelta(days=1)

    candles = _candles_diarios_ate(candle_dia, hashrate.index[0])
    sinal = strategy.generate_signal(candles)

    assert sinal.signal == Signal.SELL


def test_hold_sem_cruzamento_no_periodo_plano():
    hashrate = _serie_com_cruzamento_de_alta_e_baixa()
    strategy = HashRibbonsStrategy(hashrate)

    # dia 20: ainda no periodo plano de capitulacao, nenhum cruzamento ainda
    dia = hashrate.index[20]
    candles = _candles_diarios_ate(dia, hashrate.index[0])
    sinal = strategy.generate_signal(candles)

    assert sinal.signal == Signal.HOLD


def test_precompute_signals_bate_com_generate_signal_candle_a_candle():
    """Os dois caminhos (vetorizado, usado por simulate_backtest via
    precomputed_signals; por candle, usado em chamada direta/testes) MUST
    ficar sincronizados -- mesmo cuidado ja documentado para
    EmaRsiStrategy em backtesting/engine.py."""
    hashrate = _serie_com_cruzamento_de_alta_e_baixa()
    strategy = HashRibbonsStrategy(hashrate)
    candles = _candles_diarios_ate(hashrate.index[-1], hashrate.index[0])

    sinais_vetorizados = precompute_signals(candles, hashrate)

    for i in range(20, len(candles), 37):  # amostra candles espalhados, nao todos (custo do teste)
        sinal_por_candle = strategy.generate_signal(candles.iloc[:i + 1]).signal
        assert sinais_vetorizados.iloc[i] == sinal_por_candle


def test_teste_sanidade_zero_trades_sobre_hashrate_sem_cruzamento():
    assert mod.teste_sanidade() is True


def test_gerar_resultado_custo_zero_remove_fee_e_slippage(monkeypatch):
    capturado = {}

    def _fake_simulate_backtest(df, strategy, fee_rate, slippage_pct, precomputed_signals=None):
        capturado["fee_rate"] = fee_rate
        capturado["slippage_pct"] = slippage_pct
        return "resultado-fake"

    monkeypatch.setattr(mod, "simulate_backtest", _fake_simulate_backtest)

    hashrate = _serie_com_cruzamento_de_alta_e_baixa()
    candles = _candles_diarios_ate(hashrate.index[-1], hashrate.index[0])

    resultado = mod.gerar_resultado(candles, True, hashrate)

    assert resultado == "resultado-fake"
    assert capturado["fee_rate"] == 0.0
    assert capturado["slippage_pct"] == 0.0

    mod.gerar_resultado(candles, False, hashrate)
    assert capturado["fee_rate"] > 0.0
    assert capturado["slippage_pct"] > 0.0


def test_avaliar_none_sem_hashrate(monkeypatch):
    monkeypatch.setattr(mod, "fetch_onchain_series", lambda metric, timespan: pd.DataFrame(columns=["value"]))

    assert mod.avaliar() is None


def test_avaliar_none_sem_candles(monkeypatch):
    hashrate = _serie_com_cruzamento_de_alta_e_baixa()
    monkeypatch.setattr(mod, "fetch_onchain_series",
                         lambda metric, timespan: pd.DataFrame({"value": hashrate}))
    monkeypatch.setattr(mod, "fetch_ohlcv", lambda par, tf, limit: pd.DataFrame())

    assert mod.avaliar() is None


def test_avaliar_descarta_candles_anteriores_ao_inicio_do_hashrate(monkeypatch):
    hashrate = _serie_com_cruzamento_de_alta_e_baixa()  # comeca em 2026-01-01 UTC
    monkeypatch.setattr(mod, "fetch_onchain_series",
                         lambda metric, timespan: pd.DataFrame({"value": hashrate}))

    # candles comecam 30 dias ANTES do hashrate
    candles = _candles_diarios_ate(hashrate.index[-1], hashrate.index[0] - pd.Timedelta(days=30))
    inicio_hashrate_naive = hashrate.index[0].tz_localize(None)
    n_antes = len(candles[candles.index < inicio_hashrate_naive])
    assert n_antes > 0  # confere que o cenario de teste realmente tem candles antigos
    monkeypatch.setattr(mod, "fetch_ohlcv", lambda par, tf, limit: candles)
    monkeypatch.setattr(mod, "rodar_bateria",
                         lambda candles_filtrados, gerar, teste_sanidade: candles_filtrados)

    resultado = mod.avaliar()

    # rodar_bateria (mockado para so devolver o df recebido) nunca viu os
    # candles anteriores ao inicio real do hashrate
    assert resultado.index.min() >= inicio_hashrate_naive
