import ccxt
import pytest

from data import fetcher


def test_get_exchange_omits_credentials_when_not_configured(monkeypatch):
    # apiKey="" (nao None) faz o ccxt tratar a conta como autenticada e, em
    # versoes recentes, tentar um endpoint privado dentro de fetch_markets()
    # que falha sem credencial real -- quebrando ate dados publicos (candles).
    monkeypatch.setattr(fetcher, "BINANCE_API_KEY", "")
    monkeypatch.setattr(fetcher, "BINANCE_API_SECRET", "")
    fetcher.reset_exchange_cache()  # get_exchange() agora cacheia -- sem isso o
    # segundo teste receberia a instancia deste (achado ao adicionar o cache).

    exchange = fetcher.get_exchange()

    assert exchange.apiKey is None
    assert exchange.secret is None


def test_get_exchange_passes_credentials_when_configured(monkeypatch):
    monkeypatch.setattr(fetcher, "BINANCE_API_KEY", "fake_key")
    monkeypatch.setattr(fetcher, "BINANCE_API_SECRET", "fake_secret")
    fetcher.reset_exchange_cache()

    exchange = fetcher.get_exchange()

    assert exchange.apiKey == "fake_key"
    assert exchange.secret == "fake_secret"


def test_get_exchange_returns_same_instance_on_repeated_calls():
    fetcher.reset_exchange_cache()

    first = fetcher.get_exchange()
    second = fetcher.get_exchange()

    assert first is second


def test_get_exchange_caches_sandbox_and_production_separately():
    fetcher.reset_exchange_cache()

    production = fetcher.get_exchange(sandbox=False)
    sandbox = fetcher.get_exchange(sandbox=True)

    assert production is not sandbox
    assert fetcher.get_exchange(sandbox=False) is production
    assert fetcher.get_exchange(sandbox=True) is sandbox


def test_reset_exchange_cache_forces_new_instance():
    fetcher.reset_exchange_cache()
    first = fetcher.get_exchange()

    fetcher.reset_exchange_cache()
    second = fetcher.get_exchange()

    assert first is not second


class _FlakyExchange:
    def __init__(self, fail_times, error_cls):
        self.fail_times = fail_times
        self.error_cls = error_cls
        self.calls = 0

    def fetch_ticker(self, symbol):
        self.calls += 1
        if self.calls <= self.fail_times:
            raise self.error_cls("limite de taxa da Binance")
        return {"symbol": symbol, "last": 100.0}

    def fetch_tickers(self):
        self.calls += 1
        if self.calls <= self.fail_times:
            raise self.error_cls("limite de taxa da Binance")
        return {"BTC/USDT": {"last": 100.0}}


def test_fetch_ticker_retries_once_on_rate_limit_exceeded_then_succeeds(monkeypatch):
    exchange = _FlakyExchange(fail_times=1, error_cls=ccxt.RateLimitExceeded)
    monkeypatch.setattr(fetcher, "get_exchange", lambda sandbox=False: exchange)
    monkeypatch.setattr(fetcher.time, "sleep", lambda seconds: None)

    result = fetcher.fetch_ticker("BTC/USDT")

    assert result == {"symbol": "BTC/USDT", "last": 100.0}
    assert exchange.calls == 2


def test_fetch_tickers_retries_once_on_rate_limit_exceeded_then_succeeds(monkeypatch):
    # Achado de code-review: get_top_pairs() (backtesting/scanner.py) chama
    # fetch_tickers() (plural, busca todos os mercados de uma vez -- a
    # requisicao mais pesada do projeto, a mais provavel de esbarrar em rate
    # limit) e precisa do mesmo retry que fetch_ticker() singular ja tem.
    exchange = _FlakyExchange(fail_times=1, error_cls=ccxt.RateLimitExceeded)
    monkeypatch.setattr(fetcher, "get_exchange", lambda sandbox=False: exchange)
    monkeypatch.setattr(fetcher.time, "sleep", lambda seconds: None)

    result = fetcher.fetch_tickers()

    assert result == {"BTC/USDT": {"last": 100.0}}
    assert exchange.calls == 2


def test_fetch_ticker_retries_on_ddos_protection_then_succeeds(monkeypatch):
    # HTTP 418 da Binance vira ccxt.DDoSProtection -- classe irma de
    # RateLimitExceeded (HTTP 429), nao subclasse -- as duas precisam disparar
    # retry (ver research.md).
    exchange = _FlakyExchange(fail_times=1, error_cls=ccxt.DDoSProtection)
    monkeypatch.setattr(fetcher, "get_exchange", lambda sandbox=False: exchange)
    monkeypatch.setattr(fetcher.time, "sleep", lambda seconds: None)

    result = fetcher.fetch_ticker("BTC/USDT")

    assert result == {"symbol": "BTC/USDT", "last": 100.0}


def test_fetch_ticker_propagates_after_exhausting_retries(monkeypatch):
    exchange = _FlakyExchange(fail_times=99, error_cls=ccxt.RateLimitExceeded)
    monkeypatch.setattr(fetcher, "get_exchange", lambda sandbox=False: exchange)
    sleep_calls = []
    monkeypatch.setattr(fetcher.time, "sleep", lambda seconds: sleep_calls.append(seconds))

    with pytest.raises(ccxt.RateLimitExceeded):
        fetcher.fetch_ticker("BTC/USDT")

    assert exchange.calls == 3  # numero maximo de tentativas (FR-007)
    assert len(sleep_calls) == 2  # espera entre tentativa 1->2 e 2->3, nao apos a ultima


class _PaginatedFakeExchange:
    """Simula o teto real da Binance de ~1000 candles por chamada -- cada
    fetch_ohlcv com since= retorna no maximo 1000, exigindo paginacao para
    limits maiores."""

    def __init__(self, total_available=2500, timeframe_seconds=14400):
        self._timeframe_seconds = timeframe_seconds
        self._now_ms = 1_800_000_000_000
        step_ms = timeframe_seconds * 1000
        self._all_candles = [
            [self._now_ms - (total_available - i) * step_ms, 100.0, 101.0, 99.0, 100.5, 10.0]
            for i in range(total_available)
        ]
        self.calls = []

    def parse_timeframe(self, timeframe):
        return self._timeframe_seconds

    def milliseconds(self):
        return self._now_ms

    def fetch_ohlcv(self, symbol, timeframe, since=None, limit=None):
        self.calls.append({"since": since, "limit": limit})
        if since is None:
            return self._all_candles[-limit:] if limit else self._all_candles
        candles = [c for c in self._all_candles if c[0] >= since]
        return candles[:limit]


def test_paginacao_supera_teto_de_1000_candles_por_chamada(monkeypatch):
    fetcher._cache.clear()
    ex = _PaginatedFakeExchange(total_available=2500)
    monkeypatch.setattr(fetcher, "get_exchange", lambda *a, **k: ex)

    df = fetcher.fetch_ohlcv("BTC/USDT", "4h", limit=2000)

    assert len(df) == 2000
    assert len(ex.calls) > 1  # exigiu mais de uma chamada para reunir 2000
    assert all(c["limit"] == fetcher._EXCHANGE_MAX_CANDLES_PER_CALL for c in ex.calls)
    assert df.index.is_monotonic_increasing
    assert not df.index.has_duplicates
    fetcher._cache.clear()


def test_paginacao_para_ao_esgotar_historico_disponivel(monkeypatch):
    fetcher._cache.clear()
    ex = _PaginatedFakeExchange(total_available=1500)
    monkeypatch.setattr(fetcher, "get_exchange", lambda *a, **k: ex)

    df = fetcher.fetch_ohlcv("BTC/USDT", "4h", limit=5000)

    assert len(df) == 1500  # nao trava em loop infinito pedindo mais do que existe
    fetcher._cache.clear()


def test_limit_ate_1000_nao_usa_caminho_paginado(monkeypatch):
    fetcher._cache.clear()
    ex = _PaginatedFakeExchange(total_available=2500)
    monkeypatch.setattr(fetcher, "get_exchange", lambda *a, **k: ex)

    fetcher.fetch_ohlcv("BTC/USDT", "4h", limit=1000)

    # Caminho antigo (chamada unica com limit=, sem since=) preservado --
    # _PaginatedFakeExchange so aceita limit= no metodo real, mas o teste de
    # nao-regressao ja cobre esse caminho com _FakeExchange; aqui so
    # confirmamos que uma unica chamada foi feita.
    assert len(ex.calls) == 1
    fetcher._cache.clear()


def test_fetch_ticker_does_not_retry_on_non_rate_limit_error(monkeypatch):
    class _AlwaysFailsBadSymbol:
        def __init__(self):
            self.calls = 0

        def fetch_ticker(self, symbol):
            self.calls += 1
            raise ccxt.BadSymbol("simbolo invalido")

    exchange = _AlwaysFailsBadSymbol()
    monkeypatch.setattr(fetcher, "get_exchange", lambda sandbox=False: exchange)
    sleep_calls = []
    monkeypatch.setattr(fetcher.time, "sleep", lambda seconds: sleep_calls.append(seconds))

    with pytest.raises(ccxt.BadSymbol):
        fetcher.fetch_ticker("BTC/USDT")

    assert exchange.calls == 1  # nenhuma tentativa extra
    assert sleep_calls == []  # nenhuma espera -- erro propaga na hora
