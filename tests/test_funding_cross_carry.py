"""H24 -- diferencial de funding entre corretoras, custo/capital
corrigidos (spec 061)."""
import pandas as pd
import pytest

from backtesting import funding_cross_carry as fcc


def _hist(taxas, inicio="2026-01-01", freq="8h"):
    idx = pd.date_range(inicio, periods=len(taxas), freq=freq)
    return pd.DataFrame({"fundingRate": taxas}, index=idx)


def test_avaliar_par_corretoras_none_quando_falta_historico(monkeypatch):
    def _fake(corretora, par, dias=90):
        return pd.DataFrame(columns=["fundingRate"]) if corretora == "gate" else _hist([0.0001] * 300)
    monkeypatch.setattr(fcc, "fetch_funding_rate_history", _fake)

    assert fcc.avaliar_par_corretoras("binance", "gate", "BTC/USDT") is None


def test_avaliar_par_corretoras_none_quando_cobertura_abaixo_do_piso(monkeypatch):
    curto = _hist([0.0001] * 3)  # ~1 dia
    monkeypatch.setattr(fcc, "fetch_funding_rate_history", lambda c, p, dias=90: curto)

    assert fcc.avaliar_par_corretoras("binance", "bybit", "BTC/USDT") is None


def test_diferencial_positivo_calcula_direcao_e_capital_implantado(monkeypatch):
    """binance sempre 0,0002 acima de bybit -- diferencial positivo,
    direcao deve vender (short) binance."""
    n = 300
    hist_a = _hist([0.0003] * n)
    hist_b = _hist([0.0001] * n)

    def _fake(corretora, par, dias=90):
        return hist_a if corretora == "binance" else hist_b
    monkeypatch.setattr(fcc, "fetch_funding_rate_history", _fake)

    r = fcc.avaliar_par_corretoras("binance", "bybit", "BTC/USDT")

    assert r is not None
    assert r.direcao == "short binance / long bybit"
    assert r.diferencial_bruto_aa > 0
    custo = 2 * (fcc.TAXA_TOMADOR["binance"] + fcc.TAXA_TOMADOR["bybit"])
    fator_anual = 365.0 / r.dias_cobertos
    assert r.diferencial_liquido_aa_nocional == pytest.approx(
        r.diferencial_bruto_aa - custo * fator_anual, abs=1e-6)
    assert r.diferencial_liquido_aa_capital_implantado == pytest.approx(
        r.diferencial_liquido_aa_nocional / 2.0)


def test_diferencial_negativo_inverte_direcao(monkeypatch):
    n = 300
    hist_a = _hist([0.0001] * n)
    hist_b = _hist([0.0004] * n)

    def _fake(corretora, par, dias=90):
        return hist_a if corretora == "okx" else hist_b
    monkeypatch.setattr(fcc, "fetch_funding_rate_history", _fake)

    r = fcc.avaliar_par_corretoras("okx", "gate", "BTC/USDT")

    assert r.direcao == "short gate / long okx"
    assert r.diferencial_bruto_aa > 0  # sempre positivo (abs), so a direcao inverte


def test_alinhamento_absorve_jitter_de_segundos(monkeypatch):
    """gate com alguns segundos de desvio do horario cheio -- ainda deve
    alinhar com a outra corretora exata."""
    n = 300
    idx_exato = pd.date_range("2026-01-01", periods=n, freq="8h")
    idx_jitter = idx_exato + pd.Timedelta(seconds=2)
    hist_a = pd.DataFrame({"fundingRate": [0.0002] * n}, index=idx_exato)
    hist_b = pd.DataFrame({"fundingRate": [0.0001] * n}, index=idx_jitter)

    def _fake(corretora, par, dias=90):
        return hist_a if corretora == "binance" else hist_b
    monkeypatch.setattr(fcc, "fetch_funding_rate_history", _fake)

    r = fcc.avaliar_par_corretoras("binance", "gate", "BTC/USDT")

    assert r is not None
    assert r.n_periodos == n  # todos os periodos alinharam apesar do jitter


def test_avaliar_universo_cobre_todas_as_combinacoes_de_corretoras(monkeypatch):
    n = 300
    hist = _hist([0.0001] * n)
    monkeypatch.setattr(fcc, "fetch_funding_rate_history", lambda c, p, dias=90: hist)

    resultados = fcc.avaliar_universo(pares=("BTC/USDT",),
                                       corretoras=("binance", "bybit", "okx"))

    # C(3,2) = 3 combinacoes, todas com diferencial zero (mesma serie) mas validas
    assert len(resultados) == 3
    pares_corretoras = {(r.corretora_a, r.corretora_b) for r in resultados}
    assert pares_corretoras == {("binance", "bybit"), ("binance", "okx"), ("bybit", "okx")}


def test_avaliar_universo_pula_combinacoes_sem_resultado(monkeypatch):
    n = 300
    hist_valido = _hist([0.0001] * n)

    def _fake(corretora, par, dias=90):
        if corretora == "gate":
            return pd.DataFrame(columns=["fundingRate"])
        return hist_valido
    monkeypatch.setattr(fcc, "fetch_funding_rate_history", _fake)

    resultados = fcc.avaliar_universo(pares=("BTC/USDT",), corretoras=("binance", "bybit", "gate"))

    # so binance-bybit sobrevive -- as outras duas combinacoes envolvem gate (vazio)
    assert len(resultados) == 1
    assert (resultados[0].corretora_a, resultados[0].corretora_b) == ("binance", "bybit")
