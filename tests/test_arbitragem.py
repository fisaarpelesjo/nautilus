"""Testes de H15 -- arbitragem entre corretoras (spec 029).

Ver specs/029-arbitragem-entre-corretoras/{spec,data-model,tasks}.md.
"""


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
