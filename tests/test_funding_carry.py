"""H8 -- arbitragem de funding rate, revisao com custo/capital corrigidos
(spec 058)."""
import pandas as pd
import pytest

from backtesting import funding_carry


def _hist(taxas, dias_span):
    """Serie de fundingRate distribuida uniformemente ao longo de dias_span."""
    n = len(taxas)
    idx = pd.date_range("2026-01-01", periods=n, freq=f"{max(1, dias_span * 24 // max(n, 1))}h")
    return pd.DataFrame({"fundingRate": taxas}, index=idx)


def test_avaliar_par_none_quando_sem_historico(monkeypatch):
    monkeypatch.setattr(funding_carry, "fetch_funding_rate_history",
                         lambda par, dias=365: pd.DataFrame(columns=["fundingRate"]))

    assert funding_carry.avaliar_par("XYZ/USDT") is None


def test_avaliar_par_none_quando_cobertura_abaixo_do_piso(monkeypatch):
    idx = pd.date_range("2026-01-01", periods=3, freq="8h")  # ~1 dia de cobertura
    hist = pd.DataFrame({"fundingRate": [0.0001, 0.0001, 0.0001]}, index=idx)
    monkeypatch.setattr(funding_carry, "fetch_funding_rate_history",
                         lambda par, dias=365: hist)

    assert funding_carry.avaliar_par("NOVO/USDT") is None


def test_avaliar_par_calcula_bruto_liquido_e_capital_implantado(monkeypatch):
    """365 dias, fundingRate constante 0,0001 a cada 8h (1095 pagamentos) --
    bruto_aa = 0,0001 * 1095 = 0,1095 (10,95% a.a.), mesma ordem de grandeza
    da taxa de referencia citada no H8 original."""
    idx = pd.date_range("2026-01-01", periods=1095, freq="8h")
    hist = pd.DataFrame({"fundingRate": [0.0001] * 1095}, index=idx)
    monkeypatch.setattr(funding_carry, "fetch_funding_rate_history",
                         lambda par, dias=365: hist)

    r = funding_carry.avaliar_par("BTC/USDT")

    assert r is not None
    # 1094*8h ~= 364,67 dias cobertos (nao exatos 365) -- fator_anual ~1,003
    # arredonda bruto ligeiramente acima de 0,1095 puro, por construcao.
    assert r.bruto_aa == pytest.approx(0.1095, abs=5e-4)
    custo_esperado = 2 * (0.001 + 0.0005) * (365.0 / r.dias_cobertos)  # 4 pernas, D1/D2
    assert r.liquido_aa_nocional == pytest.approx(r.bruto_aa - custo_esperado, abs=1e-6)
    assert r.liquido_aa_capital_implantado == pytest.approx(r.liquido_aa_nocional / 2, abs=1e-6)


def test_capital_implantado_e_metade_do_liquido_sobre_nocional(monkeypatch):
    idx = pd.date_range("2026-01-01", periods=1095, freq="8h")
    hist = pd.DataFrame({"fundingRate": [0.0003] * 1095}, index=idx)
    monkeypatch.setattr(funding_carry, "fetch_funding_rate_history",
                         lambda par, dias=365: hist)

    r = funding_carry.avaliar_par("ETH/USDT")

    assert r.liquido_aa_capital_implantado == pytest.approx(r.liquido_aa_nocional / 2.0)


def test_supera_benchmark_false_quando_capital_implantado_abaixo_do_piso(monkeypatch):
    """Replica a leitura de H8 original: bruto pequeno o bastante para o
    retorno sobre capital implantado (metade do liquido) ficar abaixo do
    piso de 5% -- caso realista de BTC (bruto ~3,37% a.a. original)."""
    idx = pd.date_range("2026-01-01", periods=1095, freq="8h")
    taxa_diaria_equiv = 0.0337 / 365  # ~3,37% a.a. bruto, espalhado
    hist = pd.DataFrame({"fundingRate": [taxa_diaria_equiv / 3] * 1095}, index=idx)
    monkeypatch.setattr(funding_carry, "fetch_funding_rate_history",
                         lambda par, dias=365: hist)

    r = funding_carry.avaliar_par("BTC/USDT")

    assert r.supera_benchmark is False


def test_supera_benchmark_true_quando_capital_implantado_acima_do_piso(monkeypatch):
    idx = pd.date_range("2026-01-01", periods=1095, freq="8h")
    hist = pd.DataFrame({"fundingRate": [0.0005] * 1095}, index=idx)  # bruto ~54,75% a.a.
    monkeypatch.setattr(funding_carry, "fetch_funding_rate_history",
                         lambda par, dias=365: hist)

    r = funding_carry.avaliar_par("ALTO/USDT")

    assert r.supera_benchmark is True


def test_avaliar_universo_pula_pares_sem_resultado(monkeypatch):
    idx = pd.date_range("2026-01-01", periods=1095, freq="8h")
    hist_valido = pd.DataFrame({"fundingRate": [0.0001] * 1095}, index=idx)

    def _fake(par, dias=365):
        if par == "SEMPERP/USDT":
            return pd.DataFrame(columns=["fundingRate"])
        return hist_valido

    monkeypatch.setattr(funding_carry, "fetch_funding_rate_history", _fake)

    resultados = funding_carry.avaliar_universo(["BTC/USDT", "SEMPERP/USDT", "ETH/USDT"])

    pares = [r.par for r in resultados]
    assert pares == ["BTC/USDT", "ETH/USDT"]
