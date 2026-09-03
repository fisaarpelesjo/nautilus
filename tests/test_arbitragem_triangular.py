"""Testes de H22 -- arbitragem triangular intra-corretora (spec 060).

Ver specs/060-h22-arbitragem-triangular/{spec,research}.md.
"""
import pytest

from backtesting import arbitragem_triangular as at


@pytest.fixture(autouse=True)
def _arquivo_tmp(tmp_path, monkeypatch):
    from data import paths as data_paths
    monkeypatch.setattr(data_paths, "ARBITRAGEM_TRIANGULAR_FILE", str(tmp_path / "tri.jsonl"))


# --------------------------------------------------------- _comprar / _vender

def test_comprar_preenche_totalmente_quando_ha_profundidade():
    niveis = [(100.0, 5.0), (101.0, 5.0)]  # 500 + 505 = 1005 de valor total
    preco_medio, gasto, qtd = at._comprar(niveis, 600.0)
    assert gasto == pytest.approx(600.0)
    assert qtd == pytest.approx(5.0 + 100.0 / 101.0)


def test_comprar_preenchimento_parcial_quando_livro_raso():
    niveis = [(100.0, 1.0)]  # so 100 de valor total
    preco_medio, gasto, qtd = at._comprar(niveis, 1000.0)
    assert gasto == pytest.approx(100.0)
    assert qtd == pytest.approx(1.0)


def test_vender_preenche_totalmente_quando_ha_profundidade():
    niveis = [(100.0, 5.0), (99.0, 5.0)]
    preco_medio, qtd_vendida, receita = at._vender(niveis, 6.0)
    assert qtd_vendida == pytest.approx(6.0)
    assert receita == pytest.approx(5 * 100.0 + 1 * 99.0)


def test_vender_preenchimento_parcial_quando_livro_raso():
    niveis = [(100.0, 1.0)]
    preco_medio, qtd_vendida, receita = at._vender(niveis, 10.0)
    assert qtd_vendida == pytest.approx(1.0)
    assert receita == pytest.approx(100.0)


def test_preenchido_dentro_da_tolerancia():
    assert at._preenchido(999.9999999, 1000.0) is True
    assert at._preenchido(900.0, 1000.0) is False
    assert at._preenchido(0.0, 0.0) is True


# --------------------------------------------------------------- medir_triangulo

class _ExchangeFalsoTriangular:
    def __init__(self, livros: dict, falhar: set = frozenset()):
        self._livros = livros
        self._falhar = falhar

    def fetch_order_book(self, par):
        if par in self._falhar:
            raise ConnectionError("timeout simulado")
        return self._livros[par]


def _livro(bid, ask, qtd=100.0):
    return {"bids": [[bid, qtd]], "asks": [[ask, qtd]]}


def test_triangulo_balanceado_sem_oportunidade_apos_custo(monkeypatch):
    """BTC/USDT=50000, ETH/BTC=0.05, ETH/USDT=2500 -- ciclo fecha em ~1.0
    bruto (sem viés), custo de 3 pernas garante diferencial liquido < 0."""
    livros = {
        "BTC/USDT": _livro(50000.0, 50000.0),
        "ETH/BTC": _livro(0.05, 0.05),
        "ETH/USDT": _livro(2500.0, 2500.0),
    }
    ex = _ExchangeFalsoTriangular(livros)
    monkeypatch.setattr(at, "get_exchange", lambda: ex)

    ciclos, indisponiveis = at.medir_triangulo(volume_usdt=10_000.0)

    assert indisponiveis == []
    assert len(ciclos) == 2
    for c in ciclos:
        assert c.diferencial_bruto_pct == pytest.approx(0.0, abs=1e-9)
        assert c.diferencial_liquido_pct < 0
        assert c.estado == "sem_oportunidade"


def test_triangulo_desbalanceado_detecta_oportunidade(monkeypatch):
    """ETH/BTC artificialmente barato no ask (comprar ETH com BTC compensa
    mais que o preco implicito de BTC/USDT x ETH/USDT) -- desbalanco maior
    que o custo de 3 pernas (0,30%) produz oportunidade na direcao direta."""
    livros = {
        "BTC/USDT": _livro(50000.0, 50000.0),
        "ETH/BTC": _livro(0.0440, 0.0440),  # implicito seria 0.05 (2500/50000)
        "ETH/USDT": _livro(2500.0, 2500.0),
    }
    ex = _ExchangeFalsoTriangular(livros)
    monkeypatch.setattr(at, "get_exchange", lambda: ex)

    ciclos, indisponiveis = at.medir_triangulo(volume_usdt=10_000.0)

    direto = next(c for c in ciclos if c.direcao == "direto")
    assert direto.diferencial_bruto_pct > 0
    assert direto.estado == "oportunidade"


def test_leg_indisponivel_aborta_o_ciclo_sem_medicao_parcial(monkeypatch):
    livros = {
        "BTC/USDT": _livro(50000.0, 50000.0),
        "ETH/BTC": _livro(0.05, 0.05),
        "ETH/USDT": _livro(2500.0, 2500.0),
    }
    ex = _ExchangeFalsoTriangular(livros, falhar={"ETH/BTC"})
    monkeypatch.setattr(at, "get_exchange", lambda: ex)

    ciclos, indisponiveis = at.medir_triangulo(volume_usdt=10_000.0)

    assert ciclos == []
    assert "ETH/BTC" in indisponiveis


def test_profundidade_insuficiente_quando_livro_raso(monkeypatch):
    livros = {
        "BTC/USDT": _livro(50000.0, 50000.0, qtd=0.001),  # so US$50 de profundidade
        "ETH/BTC": _livro(0.05, 0.05),
        "ETH/USDT": _livro(2500.0, 2500.0),
    }
    ex = _ExchangeFalsoTriangular(livros)
    monkeypatch.setattr(at, "get_exchange", lambda: ex)

    ciclos, indisponiveis = at.medir_triangulo(volume_usdt=10_000.0)

    direto = next(c for c in ciclos if c.direcao == "direto")
    assert direto.profundidade_suficiente is False
    assert direto.estado == "profundidade_insuficiente"


def test_ciclos_sao_persistidos(monkeypatch):
    from data import arbitragem_triangular_store as store

    livros = {
        "BTC/USDT": _livro(50000.0, 50000.0),
        "ETH/BTC": _livro(0.05, 0.05),
        "ETH/USDT": _livro(2500.0, 2500.0),
    }
    ex = _ExchangeFalsoTriangular(livros)
    monkeypatch.setattr(at, "get_exchange", lambda: ex)

    at.medir_triangulo(volume_usdt=10_000.0)

    observacoes = store.carregar_observacoes()
    assert len(observacoes) == 2


# ------------------------------------------------------------------- agregar

def test_agregar_conta_por_triangulo_e_direcao():
    historico = [
        {"triangulo": "BTC-ETH-USDT", "direcao": "direto"},
        {"triangulo": "BTC-ETH-USDT", "direcao": "direto"},
        {"triangulo": "BTC-ETH-USDT", "direcao": "inverso"},
    ]
    relatorio = at.agregar([], historico)
    assert relatorio.n_observacoes_por_direcao[("BTC-ETH-USDT", "direto")] == 2
    assert relatorio.n_observacoes_por_direcao[("BTC-ETH-USDT", "inverso")] == 1


def test_agregar_amostra_suficiente_exige_o_minimo_em_todas_as_direcoes():
    """Diferente de H15 (15 combinacoes independentes, usa a MAIS coberta),
    aqui as duas direcoes sao sempre medidas juntas no mesmo ciclo -- exige
    o minimo na MENOS coberta para nao superestimar cobertura."""
    historico = (
        [{"triangulo": "BTC-ETH-USDT", "direcao": "direto"}] * 35
        + [{"triangulo": "BTC-ETH-USDT", "direcao": "inverso"}] * 5
    )
    relatorio = at.agregar([], historico)
    assert relatorio.estado_agregado == "inconclusivo"


def test_agregar_amostra_suficiente_quando_ambas_direcoes_atingem_o_minimo():
    historico = (
        [{"triangulo": "BTC-ETH-USDT", "direcao": "direto"}] * 30
        + [{"triangulo": "BTC-ETH-USDT", "direcao": "inverso"}] * 30
    )
    relatorio = at.agregar([], historico)
    assert relatorio.estado_agregado == "amostra_suficiente"
