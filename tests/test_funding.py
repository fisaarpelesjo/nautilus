"""Historico de funding rate via ccxt (spec 058, H8)."""
import ccxt
import pytest

from data import funding


def test_perp_symbol_converte_par_spot_para_formato_ccxt():
    assert funding.perp_symbol("BTC/USDT") == "BTC/USDT:USDT"
    assert funding.perp_symbol("ETH/USDT") == "ETH/USDT:USDT"


class _FakeFuturesExchange:
    def __init__(self, registros, now_ms):
        self._registros = registros  # lista de {"timestamp": ms, "fundingRate": x}
        self._now_ms = now_ms
        self.calls = []

    def milliseconds(self):
        return self._now_ms

    def fetch_funding_rate_history(self, symbol, since=None, limit=None):
        self.calls.append({"since": since, "limit": limit})
        lote = [r for r in self._registros if r["timestamp"] >= since]
        return lote[:limit]


class _BadSymbolExchange:
    def milliseconds(self):
        return 1_700_000_000_000

    def fetch_funding_rate_history(self, symbol, since=None, limit=None):
        raise ccxt.BadSymbol(f"binance does not have market symbol {symbol}")


def test_par_sem_mercado_perpetuo_devolve_dataframe_vazio(monkeypatch):
    monkeypatch.setattr(funding, "_get_futures_exchange", lambda: _BadSymbolExchange())

    df = funding.fetch_funding_rate_history("SNDKB/USDT", dias=30)

    assert len(df) == 0
    assert list(df.columns) == ["fundingRate"]


def test_historico_normal_devolve_taxas_ordenadas_sem_duplicatas(monkeypatch):
    oito_horas_ms = 8 * 60 * 60 * 1000
    now = 1_700_000_000_000
    registros = [
        {"timestamp": now - 3 * oito_horas_ms, "fundingRate": 0.0001},
        {"timestamp": now - 2 * oito_horas_ms, "fundingRate": -0.0002},
        {"timestamp": now - 1 * oito_horas_ms, "fundingRate": 0.0003},
    ]
    ex = _FakeFuturesExchange(registros, now_ms=now)
    monkeypatch.setattr(funding, "_get_futures_exchange", lambda: ex)

    df = funding.fetch_funding_rate_history("BTC/USDT", dias=1)

    assert len(df) == 3
    assert df.index.is_monotonic_increasing
    assert not df.index.has_duplicates
    assert df["fundingRate"].sum() == pytest.approx(0.0002)


def test_paginacao_supera_teto_por_chamada(monkeypatch):
    oito_horas_ms = 8 * 60 * 60 * 1000
    now = 1_700_000_000_000
    n_total = 1500
    registros = [
        {"timestamp": now - (n_total - i) * oito_horas_ms, "fundingRate": 0.0001}
        for i in range(n_total)
    ]
    ex = _FakeFuturesExchange(registros, now_ms=now)
    monkeypatch.setattr(funding, "_get_futures_exchange", lambda: ex)
    monkeypatch.setattr(funding, "_MAX_RECORDS_PER_CALL", 1000)

    df = funding.fetch_funding_rate_history("BTC/USDT", dias=500)

    assert len(df) == n_total
    assert len(ex.calls) > 1


def test_reset_futures_exchange_cache_forca_nova_instancia(monkeypatch):
    instancias = []

    class _Fake:
        def __init__(self):
            instancias.append(self)

    monkeypatch.setattr(funding.ccxt, "binance", lambda config: _Fake())
    funding.reset_futures_exchange_cache()

    a = funding._get_futures_exchange()
    b = funding._get_futures_exchange()
    assert a is b

    funding.reset_futures_exchange_cache()
    c = funding._get_futures_exchange()
    assert c is not a
    funding.reset_futures_exchange_cache()
