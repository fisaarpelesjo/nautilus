"""Testes de H15 -- arbitragem entre corretoras (spec 029).

Ver specs/029-arbitragem-entre-corretoras/{spec,data-model,tasks}.md.
"""


import pytest

from backtesting import arbitragem


# ---------------------------------------------------------------------------
# Foundational: normalizar_niveis (T003)
# ---------------------------------------------------------------------------

def test_normalizar_niveis_dois_campos():
    raw = [[50000.0, 1.5], [50001.0, 2.0]]
    assert arbitragem.normalizar_niveis(raw) == [(50000.0, 1.5), (50001.0, 2.0)]


def test_normalizar_niveis_tres_campos():
    # formato kraken/okx: preco, qtd, instante do nivel -- terceiro descartado
    raw = [[50000.0, 1.5, 1725000000000], [50001.0, 2.0, 1725000000123]]
    assert arbitragem.normalizar_niveis(raw) == [(50000.0, 1.5), (50001.0, 2.0)]


def test_normalizar_niveis_vazio():
    assert arbitragem.normalizar_niveis([]) == []
    assert arbitragem.normalizar_niveis(None) == []


# ---------------------------------------------------------------------------
# Foundational: LeituraLivro / ler_livro (T005)
# ---------------------------------------------------------------------------

class _ExchangeFalso:
    def __init__(self, book=None, falha=False):
        self._book = book
        self._falha = falha
        self.config = {}

    def fetch_order_book(self, par):
        if self._falha:
            raise ConnectionError("timeout simulado")
        return self._book


def test_ler_livro_sucesso(monkeypatch):
    arbitragem.reset_exchange_cache()
    book = {"bids": [[50000.0, 1.0]], "asks": [[50001.0, 1.0]]}
    monkeypatch.setattr(arbitragem, "_get_exchange_publico", lambda c: _ExchangeFalso(book=book))

    leitura = arbitragem.ler_livro("binance", "BTC/USDT")

    assert leitura.sucesso
    assert leitura.corretora == "binance"
    assert leitura.bids == [(50000.0, 1.0)]
    assert leitura.asks == [(50001.0, 1.0)]


def test_ler_livro_falha_nao_levanta_excecao(monkeypatch):
    arbitragem.reset_exchange_cache()
    monkeypatch.setattr(arbitragem, "_get_exchange_publico", lambda c: _ExchangeFalso(falha=True))

    leitura = arbitragem.ler_livro("kraken", "BTC/USDT")

    assert not leitura.sucesso
    assert leitura.erro is not None


def test_get_exchange_publico_nunca_autenticado():
    arbitragem.reset_exchange_cache()
    exchange = arbitragem._get_exchange_publico("binance")
    assert not exchange.apiKey
    assert not exchange.secret


# ---------------------------------------------------------------------------
# US1: preco_medio_execucao (T007)
# ---------------------------------------------------------------------------

def test_preco_medio_execucao_livro_suficiente():
    niveis = [(100.0, 50.0), (101.0, 50.0)]
    preco_medio, volume_preenchido = arbitragem.preco_medio_execucao(niveis, 1000.0)
    assert preco_medio == pytest.approx(100.0)
    assert volume_preenchido == pytest.approx(1000.0)


def test_preco_medio_execucao_livro_raso():
    niveis = [(100.0, 1.0)]  # so 100 USDT de profundidade
    preco_medio, volume_preenchido = arbitragem.preco_medio_execucao(niveis, 1000.0)
    assert volume_preenchido == pytest.approx(100.0)
    assert volume_preenchido < 1000.0


def test_preco_medio_execucao_vazio():
    assert arbitragem.preco_medio_execucao([], 1000.0) == (0.0, 0.0)


def test_preco_medio_execucao_caminha_niveis():
    # primeiro nivel cobre so metade do volume pedido, precisa do segundo
    niveis = [(100.0, 5.0), (102.0, 10.0)]  # 500 USDT + resto no segundo
    preco_medio, volume_preenchido = arbitragem.preco_medio_execucao(niveis, 1000.0)
    assert volume_preenchido == pytest.approx(1000.0)
    assert preco_medio > 100.0  # pior que o topo, caminhou o livro


# ---------------------------------------------------------------------------
# US1: comparar (T008, T009)
# ---------------------------------------------------------------------------

def _leitura(corretora, ask_preco, bid_preco, qtd=100.0, instante=0.0):
    return arbitragem.LeituraLivro(
        corretora=corretora, par="BTC/USDT", instante=instante,
        bids=[(bid_preco, qtd)], asks=[(ask_preco, qtd)],
    )


def test_comparar_diferencial_liquido():
    leitura_a = _leitura("binance", ask_preco=100.0, bid_preco=99.9)
    leitura_b = _leitura("bybit", ask_preco=100.5, bid_preco=100.4)

    c = arbitragem.comparar(leitura_a, leitura_b, volume_usdt=1000.0)

    assert c.corretora_compra == "binance"
    assert c.corretora_venda == "bybit"
    assert c.diferencial_bruto_pct == pytest.approx(0.004)
    assert c.custo_pct == pytest.approx(0.002)
    assert c.diferencial_liquido_pct == pytest.approx(0.002)
    assert c.estado == "oportunidade"
    assert c.volume_preenchido_usdt == pytest.approx(1000.0)


def test_comparar_sem_oportunidade():
    # diferencial bruto positivo mas menor que o custo dos dois lados
    leitura_a = _leitura("binance", ask_preco=100.0, bid_preco=99.9)
    leitura_b = _leitura("bybit", ask_preco=100.05, bid_preco=100.04)

    c = arbitragem.comparar(leitura_a, leitura_b, volume_usdt=1000.0)

    assert c.diferencial_liquido_pct < 0
    assert c.estado == "sem_oportunidade"


def test_comparar_custo_desconhecido_nunca_vira_zero():
    leitura_a = _leitura("binance", ask_preco=100.0, bid_preco=99.9)
    leitura_b = _leitura("corretora_nao_declarada", ask_preco=100.5, bid_preco=100.4)

    c = arbitragem.comparar(leitura_a, leitura_b, volume_usdt=1000.0)

    assert c.estado == "custo_desconhecido"
    assert c.custo_pct is None
    assert c.diferencial_liquido_pct is None


def test_comparar_profundidade_insuficiente():
    leitura_a = _leitura("binance", ask_preco=100.0, bid_preco=99.9, qtd=1.0)  # 100 USDT so
    leitura_b = _leitura("bybit", ask_preco=100.5, bid_preco=100.4, qtd=1.0)

    c = arbitragem.comparar(leitura_a, leitura_b, volume_usdt=10_000.0)

    assert c.estado == "profundidade_insuficiente"
    assert c.volume_preenchido_usdt < 10_000.0


def test_comparar_ordem_estados_custo_precede_profundidade():
    # dispara profundidade insuficiente E custo desconhecido ao mesmo tempo
    leitura_a = _leitura("binance", ask_preco=100.0, bid_preco=99.9, qtd=1.0)
    leitura_b = _leitura("corretora_nao_declarada", ask_preco=100.5, bid_preco=100.4, qtd=1.0)

    c = arbitragem.comparar(leitura_a, leitura_b, volume_usdt=10_000.0)

    assert c.estado == "custo_desconhecido"


# ---------------------------------------------------------------------------
# US1: medir_ciclo (T013) -- falha isolada, FR-011
# ---------------------------------------------------------------------------

def test_medir_ciclo_falha_isolada_nao_aborta(monkeypatch):
    def _ler_livro_falso(corretora, par):
        if corretora == "kraken":
            return arbitragem.LeituraLivro(corretora=corretora, par=par, instante=0.0, erro="falha simulada")
        return _leitura(corretora, ask_preco=100.0, bid_preco=99.9, instante=0.0)

    monkeypatch.setattr(arbitragem, "ler_livro", _ler_livro_falso)

    comparacoes, indisponiveis = arbitragem.medir_ciclo("BTC/USDT", volume_usdt=1000.0)

    assert indisponiveis == ["kraken"]
    corretoras_nas_comparacoes = {c.corretora_compra for c in comparacoes} | {c.corretora_venda for c in comparacoes}
    assert "kraken" not in corretoras_nas_comparacoes
    from math import comb
    assert len(comparacoes) == comb(len(arbitragem.CORRETORAS) - 1, 2)
