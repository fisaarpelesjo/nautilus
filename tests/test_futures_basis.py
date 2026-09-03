"""Contratos futuros com vencimento fixo via ccxt (spec 059, H23)."""
from data import futures_basis


class _FakeFuturesExchange:
    def __init__(self, markets, now_ms, precos):
        self._markets = markets
        self._now_ms = now_ms
        self._precos = precos

    def load_markets(self):
        return self._markets

    def milliseconds(self):
        return self._now_ms

    def fetch_ticker(self, symbol):
        return {"last": self._precos[symbol]}


class _FakeSpotExchange:
    def __init__(self, precos):
        self._precos = precos

    def fetch_ticker(self, symbol):
        return {"last": self._precos[symbol]}


def _mercado(symbol, base, quote, expiry_ms, tipo="future", swap=False):
    return {
        "symbol": symbol, "base": base, "quote": quote, "type": tipo,
        "contract": True, "swap": swap, "expiry": expiry_ms,
        "expiryDatetime": "2026-12-25T08:00:00.000Z",
    }


def test_listar_contratos_trimestrais_filtra_por_base_quote_e_tipo(monkeypatch):
    markets = {
        "BTC/USDT:USDT-261225": _mercado("BTC/USDT:USDT-261225", "BTC", "USDT", 1798185600000),
        "ETH/USDT:USDT-261225": _mercado("ETH/USDT:USDT-261225", "ETH", "USDT", 1798185600000),
        "SOL/USDT:USDT-261225": _mercado("SOL/USDT:USDT-261225", "SOL", "USDT", 1798185600000),
        "BTC/USDT:USDT": _mercado("BTC/USDT:USDT", "BTC", "USDT", None, swap=True),  # perpetuo
        "BTC/USD:BTC-261225": _mercado("BTC/USD:BTC-261225", "BTC", "USD", 1798185600000),  # coin-margined
    }
    ex = _FakeFuturesExchange(markets, now_ms=1700000000000, precos={})
    monkeypatch.setattr(futures_basis, "_get_futures_exchange", lambda: ex)

    contratos = futures_basis.listar_contratos_trimestrais(bases=("BTC", "ETH"), quote="USDT")

    symbols = [c["symbol"] for c in contratos]
    assert symbols == ["BTC/USDT:USDT-261225", "ETH/USDT:USDT-261225"]  # nem SOL, nem perpetuo, nem coin-margined


def test_listar_contratos_ordena_por_vencimento(monkeypatch):
    markets = {
        "BTC/USDT:USDT-261225": _mercado("BTC/USDT:USDT-261225", "BTC", "USDT", 1798185600000),
        "BTC/USDT:USDT-260925": _mercado("BTC/USDT:USDT-260925", "BTC", "USDT", 1790323200000),
    }
    ex = _FakeFuturesExchange(markets, now_ms=1700000000000, precos={})
    monkeypatch.setattr(futures_basis, "_get_futures_exchange", lambda: ex)

    contratos = futures_basis.listar_contratos_trimestrais(bases=("BTC",))

    assert contratos[0]["symbol"] == "BTC/USDT:USDT-260925"  # vence primeiro
    assert contratos[1]["symbol"] == "BTC/USDT:USDT-261225"


def test_fetch_basis_snapshot_calcula_dias_ate_vencimento(monkeypatch):
    agora = 1700000000000
    vencimento = agora + 30 * 24 * 60 * 60 * 1000  # 30 dias no futuro
    contrato = {"symbol": "BTC/USDT:USDT-fake", "base": "BTC", "expiry_ms": vencimento,
                "expiry_datetime": "2026-12-25T08:00:00.000Z"}
    precos_futuro = {"BTC/USDT:USDT-fake": 82000.0}
    precos_spot = {"BTC/USDT": 81000.0}

    ex_futuros = _FakeFuturesExchange({}, now_ms=agora, precos=precos_futuro)
    ex_spot = _FakeSpotExchange(precos_spot)
    monkeypatch.setattr(futures_basis, "_get_futures_exchange", lambda: ex_futuros)
    monkeypatch.setattr(futures_basis, "get_exchange", lambda: ex_spot)

    snap = futures_basis.fetch_basis_snapshot(contrato)

    assert snap["par"] == "BTC/USDT"
    assert snap["preco_futuro"] == 82000.0
    assert snap["preco_spot"] == 81000.0
    assert abs(snap["dias_ate_vencimento"] - 30.0) < 0.01
