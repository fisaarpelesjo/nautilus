import pandas as pd
import pytest
import requests

from data import onchain


class _FakeResponse:
    def __init__(self, json_data, status_code=200):
        self._json_data = json_data
        self.status_code = status_code

    def json(self):
        return self._json_data

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(f"HTTP {self.status_code}")


def _ok_body(values):
    return {"status": "ok", "name": "Teste", "unit": "un", "period": "day", "values": values}


# ---------------------------------------------------------------- US1: busca valida

def test_fetch_onchain_series_parses_valid_response(monkeypatch):
    valores = [{"x": 1725235200, "y": 10.0}, {"x": 1725321600, "y": 20.0}]
    monkeypatch.setattr(onchain.requests, "get", lambda url, timeout=None: _FakeResponse(_ok_body(valores)))

    serie = onchain.fetch_onchain_series("n-unique-addresses")

    assert isinstance(serie.index, pd.DatetimeIndex)
    assert serie.index.is_monotonic_increasing
    assert not serie.index.has_duplicates
    assert list(serie["value"]) == [10.0, 20.0]


def test_fetch_onchain_series_requests_sampled_false_and_timespan(monkeypatch):
    capturado = {}

    def _get(url, timeout=None):
        capturado["url"] = url
        return _FakeResponse(_ok_body([{"x": 1725235200, "y": 1.0}]))

    monkeypatch.setattr(onchain.requests, "get", _get)

    onchain.fetch_onchain_series("hash-rate", timespan="90days")

    assert "sampled=false" in capturado["url"]
    assert "timespan=90days" in capturado["url"]
    assert "hash-rate" in capturado["url"]


# ---------------------------------------------------------------- US2: falha nunca vira dado inventado

def test_fetch_onchain_series_raises_on_network_failure(monkeypatch):
    def _get(url, timeout=None):
        raise requests.ConnectionError("timeout simulado")

    monkeypatch.setattr(onchain.requests, "get", _get)

    with pytest.raises(requests.ConnectionError):
        onchain.fetch_onchain_series("n-unique-addresses")


def test_fetch_onchain_series_raises_on_http_error(monkeypatch):
    monkeypatch.setattr(onchain.requests, "get", lambda url, timeout=None: _FakeResponse({}, status_code=500))

    with pytest.raises(requests.HTTPError):
        onchain.fetch_onchain_series("n-unique-addresses")


def test_fetch_onchain_series_raises_on_status_not_ok(monkeypatch):
    corpo = {"status": "error", "name": "invalid chart name"}
    monkeypatch.setattr(onchain.requests, "get", lambda url, timeout=None: _FakeResponse(corpo))

    with pytest.raises(Exception, match="error"):
        onchain.fetch_onchain_series("metrica-que-nao-existe")


# ---------------------------------------------------------------- US3: vazio-por-ausencia nao e erro

def test_fetch_onchain_series_empty_values_is_not_an_error(monkeypatch):
    monkeypatch.setattr(onchain.requests, "get", lambda url, timeout=None: _FakeResponse(_ok_body([])))

    serie = onchain.fetch_onchain_series("n-unique-addresses")

    assert len(serie) == 0
