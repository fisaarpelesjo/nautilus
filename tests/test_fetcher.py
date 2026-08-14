from data import fetcher


def test_get_exchange_omits_credentials_when_not_configured(monkeypatch):
    # apiKey="" (nao None) faz o ccxt tratar a conta como autenticada e, em
    # versoes recentes, tentar um endpoint privado dentro de fetch_markets()
    # que falha sem credencial real -- quebrando ate dados publicos (candles).
    monkeypatch.setattr(fetcher, "BINANCE_API_KEY", "")
    monkeypatch.setattr(fetcher, "BINANCE_API_SECRET", "")

    exchange = fetcher.get_exchange()

    assert exchange.apiKey is None
    assert exchange.secret is None


def test_get_exchange_passes_credentials_when_configured(monkeypatch):
    monkeypatch.setattr(fetcher, "BINANCE_API_KEY", "fake_key")
    monkeypatch.setattr(fetcher, "BINANCE_API_SECRET", "fake_secret")

    exchange = fetcher.get_exchange()

    assert exchange.apiKey == "fake_key"
    assert exchange.secret == "fake_secret"
