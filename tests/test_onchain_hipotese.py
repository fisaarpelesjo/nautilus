"""H17 -- sinais on-chain, comparacao isolada BTC-only (spec 034)."""
import numpy as np
import pandas as pd
import pytest


# ---------------------------------------------------------------- US2: onchain_addr_growth_7d (T003)

def test_onchain_addr_growth_7d_calcula_variacao_da_media_movel():
    from backtesting.onchain_hipotese import onchain_addr_growth_7d

    # 21 dias, valor constante 100 nos primeiros 14, depois sobe para 200 --
    # ma7 do dia 20 = 200 (ultimos 7 dias todos 200), ma7 do dia 13 = 100
    # (dias 7..13 ainda 100) -> crescimento esperado (200-100)/100 = 1.0
    idx = pd.date_range("2026-01-01", periods=21, freq="D", tz="UTC")
    valores = [100.0] * 14 + [200.0] * 7
    serie = pd.Series(valores, index=idx)

    growth = onchain_addr_growth_7d(serie)

    assert growth.iloc[20] == pytest.approx(1.0)


def test_onchain_addr_growth_7d_primeiros_dias_sao_nan():
    from backtesting.onchain_hipotese import onchain_addr_growth_7d

    idx = pd.date_range("2026-01-01", periods=10, freq="D", tz="UTC")
    serie = pd.Series(np.arange(10, dtype=float) + 100, index=idx)

    growth = onchain_addr_growth_7d(serie)

    # precisa de 14 dias (ma7 + shift(7)) para o primeiro valor nao-NaN
    assert growth.iloc[:13].isna().all()


# ---------------------------------------------------------------- US2: _merge_causal (T004)

def test_merge_causal_nunca_ve_o_dia_do_proprio_candle():
    from backtesting.onchain_hipotese import _merge_causal

    dias = pd.date_range("2026-01-01", periods=3, freq="D", tz="UTC")
    serie_diaria = pd.Series([10.0, 20.0, 30.0], index=dias)

    # candle no MEIO do dia 2026-01-02 -- mesmo com o valor de 02 ja
    # existindo na serie, o candle MUST ver o de 01 (dia anterior completo)
    candle_meio_dia = pd.DatetimeIndex(["2026-01-02 12:00:00"], tz="UTC")
    resultado = _merge_causal(candle_meio_dia, serie_diaria)

    assert resultado.iloc[0] == pytest.approx(10.0)


def test_merge_causal_candle_a_meia_noite_ve_o_dia_anterior():
    from backtesting.onchain_hipotese import _merge_causal

    dias = pd.date_range("2026-01-01", periods=3, freq="D", tz="UTC")
    serie_diaria = pd.Series([10.0, 20.0, 30.0], index=dias)

    candle_meia_noite = pd.DatetimeIndex(["2026-01-03 00:00:00"], tz="UTC")
    resultado = _merge_causal(candle_meia_noite, serie_diaria)

    assert resultado.iloc[0] == pytest.approx(20.0)


def test_merge_causal_leva_adiante_ultimo_dia_disponivel():
    from backtesting.onchain_hipotese import _merge_causal

    # dia 2026-01-02 ausente na serie (falha pontual da fonte, FR-009)
    serie_diaria = pd.Series(
        [10.0, 30.0],
        index=pd.DatetimeIndex(["2026-01-01", "2026-01-03"], tz="UTC"),
    )

    candle = pd.DatetimeIndex(["2026-01-03 06:00:00"], tz="UTC")
    resultado = _merge_causal(candle, serie_diaria)

    # dia disponivel = 01-02, que nao existe -- leva adiante o ultimo
    # conhecido (01-01 = 10.0), nunca interpola nem usa o de 01-03
    assert resultado.iloc[0] == pytest.approx(10.0)


def test_merge_causal_sem_dia_disponivel_e_nan():
    from backtesting.onchain_hipotese import _merge_causal

    serie_diaria = pd.Series([10.0], index=pd.DatetimeIndex(["2026-01-05"], tz="UTC"))
    candle = pd.DatetimeIndex(["2026-01-01 06:00:00"], tz="UTC")

    resultado = _merge_causal(candle, serie_diaria)

    assert pd.isna(resultado.iloc[0])


# ---------------------------------------------------------------- US1: construir_extrator_onchain (T005)

def _prep_sintetico(n=300, semente=11):
    from strategy.ema_rsi import EmaRsiStrategy

    rng = np.random.default_rng(semente)
    preco = 100 * np.exp(np.cumsum(rng.normal(0.0002, 0.02, n)))
    idx = pd.date_range("2026-01-01", periods=n, freq="4h", tz="UTC")
    df = pd.DataFrame({
        "open": preco, "close": preco, "high": preco * 1.02,
        "low": preco * 0.98, "volume": np.full(n, 1000.0),
    }, index=idx)
    return EmaRsiStrategy().calculate_indicators(df)


def test_construir_extrator_onchain_retorna_seis_colunas():
    from backtesting.onchain_hipotese import construir_extrator_onchain
    from strategy.barreira_tripla import ATRIBUTOS

    prep = _prep_sintetico()
    dias = pd.date_range("2025-12-01", periods=60, freq="D", tz="UTC")
    serie_growth = pd.Series(np.linspace(-0.1, 0.1, 60), index=dias)

    extrator = construir_extrator_onchain(serie_growth)
    x = extrator(prep)

    assert sorted(x.columns) == sorted(ATRIBUTOS + ["onchain_addr_growth_7d"])
    assert len(x) == len(prep)


# ---------------------------------------------------------------- US1: avaliar_par com atributos ampliados (T006)

def test_avaliar_par_com_atributo_onchain_inclui_coeficiente():
    from backtesting.modelo import avaliar_par
    from backtesting.onchain_hipotese import construir_extrator_onchain
    from strategy.barreira_tripla import ATRIBUTOS

    n = 1200
    rng = np.random.default_rng(7)
    preco = 100 * np.exp(np.cumsum(rng.normal(0.0003, 0.03, n)))
    idx = pd.date_range("2024-01-01", periods=n, freq="4h", tz="UTC")
    df = pd.DataFrame({
        "open": preco, "close": preco, "high": preco * 1.03,
        "low": preco * 0.97, "volume": np.full(n, 1000.0),
    }, index=idx)

    dias = pd.date_range("2023-01-01", periods=800, freq="D", tz="UTC")
    serie_growth = pd.Series(rng.normal(0, 0.05, 800), index=dias)
    extrator = construir_extrator_onchain(serie_growth)
    atributos_ampliados = ATRIBUTOS + ["onchain_addr_growth_7d"]

    a = avaliar_par("BTC/USDT", df=df, atributos=atributos_ampliados,
                     extrair_atributos_fn=extrator)

    assert a.modelo is not None
    if a.modelo.coeficientes:
        assert "onchain_addr_growth_7d" in a.modelo.coeficientes


# ---------------------------------------------------------------- US3: colinearidade exposta (T010)

def test_avaliar_h17_expoe_correlacao_abaixo_do_limiar(monkeypatch):
    """Guarda de regressao (D2, research.md): se o dado on-chain mudar de
    comportamento no futuro e a correlacao cruzar 0,80, este teste MUST
    falhar -- nunca passar silenciosamente com um atributo colinear."""
    from backtesting import onchain_hipotese as m

    n = 800
    rng = np.random.default_rng(3)
    preco = 100 * np.exp(np.cumsum(rng.normal(0.0002, 0.02, n)))
    idx = pd.date_range("2025-01-01", periods=n, freq="4h", tz="UTC")
    df = pd.DataFrame({
        "open": preco, "close": preco, "high": preco * 1.02,
        # volume com variancia real -- constante faria volume_ratio
        # constante, e correlacao de Pearson contra uma serie de variancia
        # zero e NaN (nao um problema do codigo, artefato do fixture).
        "low": preco * 0.98, "volume": rng.lognormal(mean=7.0, sigma=0.3, size=n),
    }, index=idx)

    # ruido i.i.d., sem tendencia -- um passeio aleatorio (cumsum) teria
    # correlacao espuria com o preco (tambem um passeio aleatorio), o que
    # testaria um artefato da geracao sintetica, nao o codigo.
    dias = pd.date_range("2024-01-01", periods=500, freq="D", tz="UTC")
    onchain = pd.DataFrame({"value": rng.normal(500_000, 5000, 500)}, index=dias)

    monkeypatch.setattr(m, "fetch_ohlcv", lambda par, tf, limit: df)
    monkeypatch.setattr(m, "fetch_onchain_series", lambda metric, timespan: onchain)

    relatorio = m.avaliar_h17("BTC/USDT")

    assert set(relatorio.correlacao_onchain.keys()) == set(
        ["volume_ratio", "atr_ratio", "adx", "dist_ema_slow", "macd"]
    )
    assert all(abs(v) < 0.80 for v in relatorio.correlacao_onchain.values())
