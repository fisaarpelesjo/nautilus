"""H23 -- premio de futuros com vencimento fixo, custo/capital
corrigidos (spec 059)."""
import pytest

from backtesting import basis_carry


def test_avaliar_contrato_calcula_bruto_liquido_e_capital_implantado(monkeypatch):
    """Futuro 1% acima do spot, vencendo em 36,5 dias -> basis bruto
    anualizado = 0,01 * (365/36,5) = 0,10 (10% a.a.)."""
    contrato = {"symbol": "BTC/USDT:USDT-fake", "base": "BTC"}
    snap = {
        "par": "BTC/USDT", "symbol": "BTC/USDT:USDT-fake",
        "expiry_datetime": "2026-12-25T08:00:00.000Z",
        "dias_ate_vencimento": 36.5, "preco_futuro": 80800.0, "preco_spot": 80000.0,
    }
    monkeypatch.setattr(basis_carry, "fetch_basis_snapshot", lambda c: snap)

    r = basis_carry.avaliar_contrato(contrato)

    assert r.par == "BTC/USDT"
    assert r.basis_bruto_aa == pytest.approx(0.10, abs=1e-6)
    fator_anual = 365.0 / 36.5
    custo_esperado = basis_carry.CUSTO_ABERTURA_FECHAMENTO * fator_anual
    assert r.basis_liquido_aa_nocional == pytest.approx(0.10 - custo_esperado, abs=1e-6)
    assert r.basis_liquido_aa_capital_implantado == pytest.approx(r.basis_liquido_aa_nocional / 2)


def test_supera_benchmark_true_quando_basis_grande(monkeypatch):
    contrato = {"symbol": "BTC/USDT:USDT-fake", "base": "BTC"}
    snap = {
        "par": "BTC/USDT", "symbol": "BTC/USDT:USDT-fake",
        "expiry_datetime": "2026-12-25T08:00:00.000Z",
        "dias_ate_vencimento": 90.0, "preco_futuro": 84000.0, "preco_spot": 80000.0,  # 5% em 90 dias
    }
    monkeypatch.setattr(basis_carry, "fetch_basis_snapshot", lambda c: snap)

    r = basis_carry.avaliar_contrato(contrato)

    assert r.supera_benchmark is True


def test_supera_benchmark_false_quando_basis_pequeno(monkeypatch):
    contrato = {"symbol": "BTC/USDT:USDT-fake", "base": "BTC"}
    snap = {
        "par": "BTC/USDT", "symbol": "BTC/USDT:USDT-fake",
        "expiry_datetime": "2026-12-25T08:00:00.000Z",
        "dias_ate_vencimento": 90.0, "preco_futuro": 80400.0, "preco_spot": 80000.0,  # 0,5% em 90 dias
    }
    monkeypatch.setattr(basis_carry, "fetch_basis_snapshot", lambda c: snap)

    r = basis_carry.avaliar_contrato(contrato)

    assert r.supera_benchmark is False


def test_basis_negativo_backwardation_calcula_sem_quebrar(monkeypatch):
    contrato = {"symbol": "BTC/USDT:USDT-fake", "base": "BTC"}
    snap = {
        "par": "BTC/USDT", "symbol": "BTC/USDT:USDT-fake",
        "expiry_datetime": "2026-12-25T08:00:00.000Z",
        "dias_ate_vencimento": 90.0, "preco_futuro": 79000.0, "preco_spot": 80000.0,  # futuro abaixo do spot
    }
    monkeypatch.setattr(basis_carry, "fetch_basis_snapshot", lambda c: snap)

    r = basis_carry.avaliar_contrato(contrato)

    assert r.basis_bruto_aa < 0
    assert r.supera_benchmark is False


def test_avaliar_universo_avalia_cada_contrato_listado(monkeypatch):
    contratos = [
        {"symbol": "BTC/USDT:USDT-a", "base": "BTC"},
        {"symbol": "ETH/USDT:USDT-a", "base": "ETH"},
    ]
    monkeypatch.setattr(basis_carry, "listar_contratos_trimestrais", lambda bases: contratos)

    def _fake_snapshot(c):
        return {
            "par": f"{c['base']}/USDT", "symbol": c["symbol"],
            "expiry_datetime": "2026-12-25T08:00:00.000Z",
            "dias_ate_vencimento": 90.0, "preco_futuro": 100.0, "preco_spot": 100.0,
        }
    monkeypatch.setattr(basis_carry, "fetch_basis_snapshot", _fake_snapshot)

    resultados = basis_carry.avaliar_universo()

    assert [r.par for r in resultados] == ["BTC/USDT", "ETH/USDT"]
