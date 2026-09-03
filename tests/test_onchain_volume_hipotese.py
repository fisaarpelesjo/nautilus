"""H32 -- on-chain mais rico, valor transacionado (spec 069)."""
import numpy as np
import pandas as pd
import pytest


def test_onchain_txn_volume_growth_7d_reusa_a_transformacao_de_h17():
    from backtesting.onchain_volume_hipotese import onchain_txn_volume_growth_7d

    idx = pd.date_range("2026-01-01", periods=21, freq="D", tz="UTC")
    valores = [100.0] * 14 + [200.0] * 7
    serie = pd.Series(valores, index=idx)

    growth = onchain_txn_volume_growth_7d(serie)

    assert growth.iloc[20] == pytest.approx(1.0)
    assert growth.iloc[:13].isna().all()


def _hist(colunas_extra=None):
    idx = pd.date_range("2026-01-01", periods=60, freq="4h", tz="UTC")
    rng = np.random.default_rng(1)
    df = pd.DataFrame({
        "close": 100 + np.cumsum(rng.normal(0, 1, 60)),
        "high": 101 + np.cumsum(rng.normal(0, 1, 60)),
        "low": 99 + np.cumsum(rng.normal(0, 1, 60)),
        "volume": rng.uniform(10, 20, 60),
        "atr": rng.uniform(1, 2, 60),
        "volume_ma": rng.uniform(10, 20, 60),
        "rsi": rng.uniform(30, 70, 60),
        "adx": rng.uniform(10, 40, 60),
        "atr_ratio": rng.uniform(0.01, 0.05, 60),
    }, index=idx)
    return df


def test_avaliar_h32_para_antes_de_medir_desempenho_quando_colinear(monkeypatch):
    import backtesting.onchain_volume_hipotese as mod

    df = _hist()
    monkeypatch.setattr(mod, "fetch_ohlcv", lambda par, tf, limit: df)

    dias_onchain = pd.date_range("2025-12-01", periods=90, freq="D", tz="UTC")
    serie_volume = pd.Series(np.linspace(1000, 2000, 90), index=dias_onchain)

    chamadas = {"n": 0}

    def _fake_fetch_onchain(metrica, timespan="3years"):
        chamadas["n"] += 1
        return pd.DataFrame({"value": serie_volume})

    monkeypatch.setattr(mod, "fetch_onchain_series", _fake_fetch_onchain)

    class _Strategy:
        def calculate_indicators(self, df):
            return df
    monkeypatch.setattr(mod, "EmaRsiStrategy", _Strategy)

    # forca colinearidade perfeita: extrair_atributos deve devolver algo
    # cuja correlacao com a serie de volume seja >= 0.80 -- construimos
    # extrair_atributos para devolver uma copia identica linearmente
    # relacionada ao proprio growth calculado, garantindo colinearidade.
    def _fake_extrair(prep):
        n = len(prep)
        idx = prep.index
        # atributo1 sera perfeitamente correlacionado com o merge causal
        # do onchain (mesmo valor, reindexado) -- forcado no teste
        return pd.DataFrame({"atributo1": np.arange(n, dtype=float)}, index=idx)

    monkeypatch.setattr(mod, "extrair_atributos", _fake_extrair)

    def _fake_merge_causal(indice, serie):
        # devolve uma serie perfeitamente correlacionada com np.arange
        return pd.Series(np.arange(len(indice), dtype=float), index=indice)

    monkeypatch.setattr(mod, "_merge_causal", _fake_merge_causal)

    avaliar_par_chamado = {"n": 0}
    monkeypatch.setattr(mod, "avaliar_par", lambda *a, **k: avaliar_par_chamado.update(n=1))

    relatorio = mod.avaliar_h32("BTC/USDT")

    assert relatorio.colinear is True
    assert relatorio.avaliacao_base is None
    assert relatorio.avaliacao_volume is None
    assert avaliar_par_chamado["n"] == 0  # nao chegou a avaliar desempenho


def test_avaliar_h32_prossegue_quando_nao_colinear(monkeypatch):
    import backtesting.onchain_volume_hipotese as mod

    df = _hist()
    monkeypatch.setattr(mod, "fetch_ohlcv", lambda par, tf, limit: df)

    dias_onchain = pd.date_range("2025-12-01", periods=90, freq="D", tz="UTC")
    serie_volume = pd.Series(np.linspace(1000, 2000, 90), index=dias_onchain)
    monkeypatch.setattr(mod, "fetch_onchain_series",
                         lambda metrica, timespan="3years": pd.DataFrame({"value": serie_volume}))

    class _Strategy:
        def calculate_indicators(self, df):
            return df
    monkeypatch.setattr(mod, "EmaRsiStrategy", _Strategy)

    rng = np.random.default_rng(7)

    def _fake_extrair(prep):
        n = len(prep)
        return pd.DataFrame({"atributo1": rng.normal(0, 1, n)}, index=prep.index)
    monkeypatch.setattr(mod, "extrair_atributos", _fake_extrair)

    def _fake_merge_causal(indice, serie):
        return pd.Series(rng.normal(100, 1, len(indice)), index=indice)
    monkeypatch.setattr(mod, "_merge_causal", _fake_merge_causal)

    chamadas = []
    monkeypatch.setattr(mod, "avaliar_par", lambda *a, **k: chamadas.append(k) or "avaliacao")

    relatorio = mod.avaliar_h32("BTC/USDT")

    assert relatorio.colinear is False
    assert relatorio.avaliacao_base == "avaliacao"
    assert relatorio.avaliacao_volume == "avaliacao"
    assert len(chamadas) == 2  # sem atributo + com atributo
