import pandas as pd

from backtesting import reversao_pos_liquidacao as mod
from strategy.base import Signal
from strategy.reversao_pos_liquidacao import ReversaoPosLiquidacaoStrategy


def _df(rows, freq="4h"):
    idx = pd.date_range("2026-01-01", periods=len(rows), freq=freq)
    return pd.DataFrame(rows, index=idx)


def _linha_base():
    # Candle "normal": range moderado, volume constante -- warmup neutro
    # para volume_ma e ATR, sem bater nenhum dos criterios D1/D2.
    return {"open": 100.0, "high": 101.0, "low": 99.0, "close": 100.5, "volume": 100.0}


def _df_com_ultima_linha(ultima: dict, n_base: int = 24) -> pd.DataFrame:
    rows = [_linha_base() for _ in range(n_base)]
    rows.append(ultima)
    return _df(rows)


def test_buy_quando_pavio_volume_e_recuperacao_batem_simultaneamente():
    df = _df_com_ultima_linha({
        "open": 100.0, "high": 103.0, "low": 95.0, "close": 102.0, "volume": 350.0,
    })

    sinal = ReversaoPosLiquidacaoStrategy().generate_signal(df)

    assert sinal.signal == Signal.BUY


def test_hold_quando_pavio_insuficiente():
    # range=5 (98->103), pavio = min(100,102)-98 = 2 -> 2/5=0.4 < 0.5 (D1)
    df = _df_com_ultima_linha({
        "open": 100.0, "high": 103.0, "low": 98.0, "close": 102.0, "volume": 350.0,
    })

    sinal = ReversaoPosLiquidacaoStrategy().generate_signal(df)

    assert sinal.signal == Signal.HOLD


def test_hold_quando_volume_insuficiente():
    # mesmo candle valido em pavio/recuperacao, volume abaixo de 3x a media (D2)
    df = _df_com_ultima_linha({
        "open": 100.0, "high": 103.0, "low": 95.0, "close": 102.0, "volume": 250.0,
    })

    sinal = ReversaoPosLiquidacaoStrategy().generate_signal(df)

    assert sinal.signal == Signal.HOLD


def test_hold_quando_fechamento_nao_e_de_recuperacao():
    # pavio e volume batem, mas close < open -- nao e "recuperacao"
    df = _df_com_ultima_linha({
        "open": 102.0, "high": 103.0, "low": 95.0, "close": 100.0, "volume": 350.0,
    })

    sinal = ReversaoPosLiquidacaoStrategy().generate_signal(df)

    assert sinal.signal == Signal.HOLD


def test_hold_durante_warmup_sem_media_de_volume_completa():
    # menos linhas que o warmup exigido (JANELA_MEDIA_VOLUME=20, ATR=14)
    df = _df_com_ultima_linha({
        "open": 100.0, "high": 103.0, "low": 95.0, "close": 102.0, "volume": 350.0,
    }, n_base=5)

    sinal = ReversaoPosLiquidacaoStrategy().generate_signal(df)

    assert sinal.signal == Signal.HOLD


def test_gerar_resultado_custo_zero_remove_fee_e_slippage(monkeypatch):
    capturado = {}

    def _fake_simulate_backtest(df, strategy, fee_rate, slippage_pct):
        capturado["fee_rate"] = fee_rate
        capturado["slippage_pct"] = slippage_pct
        return "resultado-fake"

    monkeypatch.setattr(mod, "simulate_backtest", _fake_simulate_backtest)

    df = _df_com_ultima_linha({
        "open": 100.0, "high": 103.0, "low": 95.0, "close": 102.0, "volume": 350.0,
    })

    resultado = mod.gerar_resultado(df, True)

    assert resultado == "resultado-fake"
    assert capturado["fee_rate"] == 0.0
    assert capturado["slippage_pct"] == 0.0

    mod.gerar_resultado(df, False)
    assert capturado["fee_rate"] > 0.0
    assert capturado["slippage_pct"] > 0.0


def test_teste_sanidade_zero_trades_sobre_serie_sem_padrao():
    assert mod.teste_sanidade() is True


def test_avaliar_par_none_quando_fetch_devolve_vazio(monkeypatch):
    monkeypatch.setattr(mod, "fetch_ohlcv", lambda par, tf, limit: pd.DataFrame())

    assert mod.avaliar_par("BTC/USDT") is None


def test_avaliar_par_roda_a_bateria_com_dados_mockados(monkeypatch):
    df = _df_com_ultima_linha({
        "open": 100.0, "high": 103.0, "low": 95.0, "close": 102.0, "volume": 350.0,
    }, n_base=500)

    monkeypatch.setattr(mod, "fetch_ohlcv", lambda par, tf, limit: df)

    relatorio = mod.avaliar_par("BTC/USDT")

    assert relatorio is not None
    assert relatorio.e1_sanidade_ok is True
    assert relatorio.e2_janela_unica is not None


def test_avaliar_universo_pula_pares_sem_resultado(monkeypatch):
    def _fake_avaliar_par(par, timeframe=mod.TIMEFRAME, n_candles=mod.N_CANDLES):
        return None if par == "SEM/DADO" else object()

    monkeypatch.setattr(mod, "avaliar_par", _fake_avaliar_par)

    resultados = mod.avaliar_universo(["BTC/USDT", "SEM/DADO"])

    assert list(resultados.keys()) == ["BTC/USDT"]
