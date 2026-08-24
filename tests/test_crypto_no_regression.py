"""Contrato de nao-regressao do caminho cripto (spec 023, T003/T010).

ESTE ARQUIVO FOI ESCRITO ANTES DO REFACTOR, DE PROPOSITO. Ele fixa o
comportamento observavel de `fetch_ohlcv` para cripto COMO ELE ERA antes da
abstracao multi-mercado, e roda de novo depois dela. Escrito na ordem inversa,
viraria teste do codigo novo e perderia justamente a capacidade de provar
equivalencia.

A motivacao e concreta: este projeto ja foi atingido duas vezes pelo padrao de
dois pontos do sistema discordando em silencio -- o backtest simulando uma
estrategia sem trailing stop enquanto a producao usava trailing (spec 019), e o
replay comparando preco historico contra a EMA de hoje (spec 020). Nos dois
casos o defeito passou despercebido por nao existir teste comparando os
caminhos. Uma abstracao de fonte de dados e exatamente a oportunidade de
repetir o padrao.
"""
import pandas as pd
import pytest

from data import fetcher


class _FakeExchange:
    """Exchange dublê que registra como foi chamada, para verificar a politica
    de cache incremental sem tocar a rede."""

    def __init__(self, candles=None):
        self.calls = []
        self._candles = candles or [
            [1_700_000_000_000 + i * 3_600_000, 100.0 + i, 101.0 + i, 99.0 + i, 100.5 + i, 10.0 + i]
            for i in range(10)
        ]

    def fetch_ohlcv(self, symbol, timeframe, limit=None):
        self.calls.append({"symbol": symbol, "timeframe": timeframe, "limit": limit})
        return self._candles[-limit:] if limit else self._candles


@pytest.fixture(autouse=True)
def _limpa_cache():
    """Cache e global no modulo -- sem isolamento, um teste vaza estado para o
    proximo e o de cache incremental passa por acidente."""
    fetcher._cache.clear()
    yield
    fetcher._cache.clear()


def test_formato_do_dataframe_permanece(monkeypatch):
    monkeypatch.setattr(fetcher, "get_exchange", lambda *a, **k: _FakeExchange())

    df = fetcher.fetch_ohlcv("BTC/USDT", "4h", limit=10)

    assert list(df.columns) == ["open", "high", "low", "close", "volume"]
    assert isinstance(df.index, pd.DatetimeIndex)
    assert df.index.is_monotonic_increasing
    assert not df.index.has_duplicates


def test_primeira_chamada_busca_o_limit_pedido(monkeypatch):
    ex = _FakeExchange()
    monkeypatch.setattr(fetcher, "get_exchange", lambda *a, **k: ex)

    fetcher.fetch_ohlcv("BTC/USDT", "4h", limit=10)

    assert len(ex.calls) == 1
    assert ex.calls[0]["limit"] == 10


def test_chamada_seguinte_busca_apenas_5_e_faz_merge(monkeypatch):
    # A politica de cache incremental e o que mantem o ciclo de 60s barato --
    # buscar `limit` candles a cada chamada custaria ~5s por par.
    ex = _FakeExchange()
    monkeypatch.setattr(fetcher, "get_exchange", lambda *a, **k: ex)

    fetcher.fetch_ohlcv("BTC/USDT", "4h", limit=10)
    fetcher.fetch_ohlcv("BTC/USDT", "4h", limit=10)

    assert len(ex.calls) == 2
    assert ex.calls[1]["limit"] == 5


def test_cache_e_indexado_por_symbol_e_timeframe(monkeypatch):
    ex = _FakeExchange()
    monkeypatch.setattr(fetcher, "get_exchange", lambda *a, **k: ex)

    fetcher.fetch_ohlcv("BTC/USDT", "4h", limit=10)
    fetcher.fetch_ohlcv("BTC/USDT", "1h", limit=10)

    # Timeframes diferentes MUST NOT compartilhar entrada de cache.
    assert "BTC/USDT_4h" in fetcher._cache
    assert "BTC/USDT_1h" in fetcher._cache


def test_excecao_da_exchange_propaga(monkeypatch):
    class _Explode:
        def fetch_ohlcv(self, *a, **k):
            raise RuntimeError("falha de rede")

    monkeypatch.setattr(fetcher, "get_exchange", lambda *a, **k: _Explode())

    # Falha de dado MUST propagar -- nunca virar DataFrame vazio silencioso.
    with pytest.raises(RuntimeError):
        fetcher.fetch_ohlcv("BTC/USDT", "4h", limit=10)


def test_merge_nao_duplica_candles_repetidos(monkeypatch):
    ex = _FakeExchange()
    monkeypatch.setattr(fetcher, "get_exchange", lambda *a, **k: ex)

    fetcher.fetch_ohlcv("BTC/USDT", "4h", limit=10)
    df = fetcher.fetch_ohlcv("BTC/USDT", "4h", limit=10)

    assert not df.index.has_duplicates
