import numpy as np
import pandas as pd
import pytest

from backtesting.lead_lag import (
    _sinais_lead_lag,
    avaliar_lead_lag,
    btc_retorno_no_candle,
    resumo_consistencia,
)
from strategy.base import Signal


def _idx(n, freq="4h"):
    return pd.date_range("2026-01-01", periods=n, freq=freq)


def _df_sintetico(n=200, semente=7):
    rng = np.random.default_rng(semente)
    preco = 100 * np.exp(np.cumsum(rng.normal(0.0002, 0.02, n)))
    idx = _idx(n)
    return pd.DataFrame({
        "open": preco, "close": preco, "high": preco * 1.02,
        "low": preco * 0.98, "volume": np.full(n, 1000.0),
    }, index=idx)


# ============================================================ T001/T002

def test_sinal_dispara_exatamente_onde_retorno_btc_e_positivo():
    idx = _idx(5)
    retorno_btc = pd.Series([0.01, -0.01, 0.0, 0.02, -0.005], index=idx)

    sinais = _sinais_lead_lag(retorno_btc, idx)

    assert list(sinais) == [Signal.BUY, Signal.HOLD, Signal.HOLD, Signal.BUY, Signal.HOLD]


def test_candle_sem_retorno_de_btc_correspondente_fica_sem_sinal():
    idx_alt = _idx(4)
    # retorno_btc so cobre os 2 primeiros candles da altcoin.
    retorno_btc = pd.Series([0.01, 0.02], index=idx_alt[:2])

    sinais = _sinais_lead_lag(retorno_btc, idx_alt)

    assert sinais.iloc[2] == Signal.HOLD
    assert sinais.iloc[3] == Signal.HOLD


# ==================================================================== T003

def test_sinal_em_t_nao_depende_de_candles_posteriores_a_t():
    idx = _idx(5)
    retorno_btc_original = pd.Series([0.01, -0.01, 0.02, -0.02, 0.03], index=idx)
    retorno_btc_alterado = retorno_btc_original.copy()
    # Altera candles POSTERIORES ao indice 1 -- o sinal em t=1 nao pode mudar.
    retorno_btc_alterado.iloc[2:] = [-0.5, 0.5, -0.5]

    sinais_original = _sinais_lead_lag(retorno_btc_original, idx)
    sinais_alterado = _sinais_lead_lag(retorno_btc_alterado, idx)

    assert sinais_original.iloc[0] == sinais_alterado.iloc[0]
    assert sinais_original.iloc[1] == sinais_alterado.iloc[1]


# ==================================================================== T004

def test_retorno_btc_usa_o_mesmo_candle_nao_um_deslocamento_extra():
    """Regressao contra o erro de defasagem capturado em research.md D1:
    o retorno na linha t MUST ser close[t]/close[t-1]-1, nao
    close[t-1]/close[t-2]-1."""
    idx = _idx(4)
    close = pd.Series([100.0, 110.0, 99.0, 105.0], index=idx)

    retorno = btc_retorno_no_candle(close)

    # retorno[1] = close[1]/close[0]-1 = 0.10 (NAO retorno[0], que seria NaN)
    assert retorno.iloc[1] == pytest.approx(0.10)
    # retorno[2] = close[2]/close[1]-1 = 99/110-1 (NAO close[1]/close[0]-1)
    assert retorno.iloc[2] == pytest.approx(99.0 / 110.0 - 1.0)


# ==================================================================== T005

def test_avaliar_lead_lag_sem_rede_usa_simular_com_sinais():
    df_alt = _df_sintetico()
    retorno_btc = pd.Series(0.01, index=df_alt.index)  # sempre positivo -> sempre BUY

    resultado = avaliar_lead_lag("ALT/USDT", df_alt=df_alt, retorno_btc=retorno_btc)

    assert resultado is not None
    assert resultado.total_trades >= 0  # produzido sem excecao


def test_avaliar_lead_lag_sem_sinal_produz_zero_trades():
    df_alt = _df_sintetico()
    retorno_btc = pd.Series(-0.01, index=df_alt.index)  # sempre negativo -> nunca BUY

    resultado = avaliar_lead_lag("ALT/USDT", df_alt=df_alt, retorno_btc=retorno_btc)

    assert resultado is not None
    assert resultado.total_trades == 0


# ==================================================================== T006

def test_resultado_aceito_por_evaluate_approval_sem_excecao():
    from backtesting.approval import evaluate_approval

    df_alt = _df_sintetico()
    retorno_btc = pd.Series(0.01, index=df_alt.index)

    resultado = avaliar_lead_lag("ALT/USDT", df_alt=df_alt, retorno_btc=retorno_btc)
    veredito = evaluate_approval(resultado)

    assert veredito.status in {"aprovado", "reprovado", "inconclusivo"}


# ==================================================================== T009

def test_resumo_consistencia_conta_corretamente():
    from unittest.mock import MagicMock

    r1 = MagicMock(total_return_pct=5.0, buy_hold_return_pct=2.0, profit_factor=1.5)
    r2 = MagicMock(total_return_pct=-3.0, buy_hold_return_pct=-1.0, profit_factor=0.8)
    r3 = MagicMock(total_return_pct=1.0, buy_hold_return_pct=1.5, profit_factor=1.2)

    resumo = resumo_consistencia([("A/USDT", r1), ("B/USDT", r2), ("C/USDT", None), ("D/USDT", r3)])

    assert resumo["n_pares"] == 3
    assert resumo["supera_buy_hold"] == 1
    assert resumo["profit_factor_acima_de_1"] == 2


# ==================================================================== T010

def test_run_lead_lag_scan_busca_btc_uma_unica_vez(monkeypatch):
    from unittest.mock import MagicMock

    chamadas = []

    def fake_fetch_ohlcv(par, timeframe, limit):
        chamadas.append(par)
        return _df_sintetico()

    monkeypatch.setattr("data.fetcher.fetch_ohlcv", fake_fetch_ohlcv)
    import backtesting.lead_lag as ll
    monkeypatch.setattr(ll, "avaliar_lead_lag", lambda par, retorno_btc=None: MagicMock())

    ll.run_lead_lag_scan(pares=["A/USDT", "B/USDT", "C/USDT"])

    assert chamadas.count("BTC/USDT") == 1
