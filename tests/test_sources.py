"""Contrato de fonte de dados (spec 023, T006/T014).

Toda fonte plugavel atras de fetch_ohlcv() precisa cumprir o mesmo contrato,
para que os ~10 consumidores (backtest, compare, scan, optimize, validation,
replay, runner, chart, selector, diagnostics) nao saibam qual respondeu.
Ver specs/023-dados-multi-mercado/contracts/data-source.md.
"""
import pandas as pd
import pytest

from data import sources
from data.sources import yfinance_source


# ------------------------------------------------------------- registro de fontes

def test_registro_resolve_fonte_por_mercado():
    assert sources.get_source("crypto").name == "ccxt"
    for mercado in ["stocks_us", "stocks_br", "forex", "futures", "index"]:
        assert sources.get_source(mercado).name == "yfinance"


def test_mercado_sem_fonte_registrada_falha_explicitamente():
    with pytest.raises(ValueError):
        sources.get_source("mercado_inexistente")


# --------------------------------------------------- normalizacao e formato de saida

def _yf_df(n=10, capitalizado=True):
    """DataFrame no formato cru do yfinance -- colunas capitalizadas."""
    idx = pd.date_range("2026-01-01", periods=n, freq="4h")
    cols = ["Open", "High", "Low", "Close", "Volume"] if capitalizado else ["open", "high", "low", "close", "volume"]
    return pd.DataFrame(
        {c: [100.0 + i for i in range(n)] for c in cols},
        index=idx,
    )


def test_normaliza_colunas_para_minusculas(monkeypatch):
    # yfinance devolve Open/High/Low/Close/Volume -- a normalizacao e
    # responsabilidade da FONTE, nao do consumidor.
    monkeypatch.setattr(yfinance_source, "_download", lambda *a, **k: _yf_df())

    df = yfinance_source.YFinanceSource().fetch_ohlcv("AAPL", "4h", limit=10)

    assert list(df.columns) == ["open", "high", "low", "close", "volume"]


def test_indice_ordenado_e_sem_duplicatas(monkeypatch):
    desordenado = _yf_df(10)
    desordenado = pd.concat([desordenado.iloc[5:], desordenado.iloc[:6]])  # fora de ordem + 1 duplicata
    monkeypatch.setattr(yfinance_source, "_download", lambda *a, **k: desordenado)

    df = yfinance_source.YFinanceSource().fetch_ohlcv("AAPL", "4h", limit=10)

    assert df.index.is_monotonic_increasing
    assert not df.index.has_duplicates


# ------------------------------------------------------------------ politica de falha

def test_zero_candles_levanta_excecao(monkeypatch):
    # MUST NOT devolver DataFrame vazio -- dado ausente nunca vira resultado.
    monkeypatch.setattr(yfinance_source, "_download", lambda *a, **k: pd.DataFrame())

    with pytest.raises(ValueError, match="AAPL"):
        yfinance_source.YFinanceSource().fetch_ohlcv("AAPL", "4h", limit=10)


def test_timeframe_nao_suportado_e_recusado_nomeando_o_intervalo():
    with pytest.raises(ValueError, match="7h"):
        yfinance_source.YFinanceSource().fetch_ohlcv("AAPL", "7h", limit=10)


def test_falha_de_rede_propaga(monkeypatch):
    def _explode(*a, **k):
        raise RuntimeError("timeout")

    monkeypatch.setattr(yfinance_source, "_download", _explode)

    with pytest.raises(RuntimeError):
        yfinance_source.YFinanceSource().fetch_ohlcv("AAPL", "4h", limit=10)


def test_limit_nao_atendido_e_detectavel(monkeypatch):
    # Risco tecnico 3 de research.md: a fonte nao-cripto tem teto de 730 dias.
    # Pedir 2000 e receber 993 e normal -- mas passar silencioso desbalancearia
    # uma comparacao cripto x acoes sem ninguem notar.
    monkeypatch.setattr(yfinance_source, "_download", lambda *a, **k: _yf_df(50))

    fonte = yfinance_source.YFinanceSource()
    df = fonte.fetch_ohlcv("AAPL", "4h", limit=2000)

    assert len(df) == 50
    assert fonte.last_shortfall is not None
    assert fonte.last_shortfall["requested"] == 2000
    assert fonte.last_shortfall["received"] == 50


def test_sem_shortfall_quando_limit_e_atendido(monkeypatch):
    monkeypatch.setattr(yfinance_source, "_download", lambda *a, **k: _yf_df(10))

    fonte = yfinance_source.YFinanceSource()
    fonte.fetch_ohlcv("AAPL", "4h", limit=10)

    assert fonte.last_shortfall is None
