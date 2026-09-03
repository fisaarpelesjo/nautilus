"""Historico de funding rate multi-corretora via ccxt (spec 061, H24)."""
import ccxt

from data import funding_cross


def test_perp_symbol_converte_par_spot_para_formato_ccxt():
    assert funding_cross.perp_symbol("BTC/USDT") == "BTC/USDT:USDT"


def test_corretoras_qualificadas_nao_inclui_kraken():
    assert "kraken" not in funding_cross.CORRETORAS_QUALIFICADAS
    assert "krakenfutures" not in funding_cross.CORRETORAS_QUALIFICADAS
    assert len(funding_cross.CORRETORAS_QUALIFICADAS) == 5


def test_taxa_tomador_tem_entrada_para_cada_corretora_qualificada():
    for corretora in funding_cross.CORRETORAS_QUALIFICADAS:
        assert corretora in funding_cross.TAXA_TOMADOR
        assert 0 < funding_cross.TAXA_TOMADOR[corretora] < 0.01


class _FakeExchange:
    def __init__(self, registros, now_ms):
        self._registros = registros
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
        raise ccxt.BadSymbol(f"no market symbol {symbol}")


def test_par_sem_mercado_perpetuo_devolve_dataframe_vazio(monkeypatch):
    funding_cross.reset_exchange_cache()
    monkeypatch.setattr(funding_cross, "_get_exchange", lambda c: _BadSymbolExchange())

    df = funding_cross.fetch_funding_rate_history("bybit", "XYZ/USDT", dias=30)

    assert len(df) == 0
    assert list(df.columns) == ["fundingRate"]
    funding_cross.reset_exchange_cache()


def test_historico_normal_ordenado_sem_duplicatas(monkeypatch):
    funding_cross.reset_exchange_cache()
    oito_h = 8 * 60 * 60 * 1000
    now = 1_700_000_000_000
    registros = [
        {"timestamp": now - 3 * oito_h, "fundingRate": 0.0001},
        {"timestamp": now - 2 * oito_h, "fundingRate": -0.0002},
        {"timestamp": now - 1 * oito_h, "fundingRate": 0.0003},
    ]
    ex = _FakeExchange(registros, now_ms=now)
    monkeypatch.setattr(funding_cross, "_get_exchange", lambda c: ex)

    df = funding_cross.fetch_funding_rate_history("okx", "BTC/USDT", dias=1)

    assert len(df) == 3
    assert df.index.is_monotonic_increasing
    assert not df.index.has_duplicates
    funding_cross.reset_exchange_cache()


def test_paginacao_supera_teto_por_chamada(monkeypatch):
    funding_cross.reset_exchange_cache()
    oito_h = 8 * 60 * 60 * 1000
    now = 1_700_000_000_000
    n_total = 1500
    registros = [
        {"timestamp": now - (n_total - i) * oito_h, "fundingRate": 0.0001}
        for i in range(n_total)
    ]
    ex = _FakeExchange(registros, now_ms=now)
    monkeypatch.setattr(funding_cross, "_get_exchange", lambda c: ex)
    monkeypatch.setattr(funding_cross, "_MAX_RECORDS_PER_CALL", 1000)

    df = funding_cross.fetch_funding_rate_history("gate", "BTC/USDT", dias=500)

    assert len(df) == n_total
    assert len(ex.calls) > 1
    funding_cross.reset_exchange_cache()


def test_reset_exchange_cache_forca_nova_instancia(monkeypatch):
    instancias = []

    class _Fake:
        def __init__(self, cfg):
            instancias.append(self)

    monkeypatch.setattr(funding_cross.ccxt, "binance", lambda cfg: _Fake(cfg))
    funding_cross.reset_exchange_cache()

    a = funding_cross._get_exchange("binance")
    b = funding_cross._get_exchange("binance")
    assert a is b

    funding_cross.reset_exchange_cache()
    c = funding_cross._get_exchange("binance")
    assert c is not a
    funding_cross.reset_exchange_cache()
