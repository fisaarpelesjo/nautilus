from execution import reconciliation


class _FakeExchange:
    def __init__(self, totals, prices=None, fail_ticker=False):
        self._totals = totals
        self._prices = prices or {}
        self._fail_ticker = fail_ticker

    def fetch_balance(self):
        return {"total": dict(self._totals)}

    def fetch_ticker(self, symbol):
        if self._fail_ticker:
            raise RuntimeError("ticker indisponivel")
        return {"last": self._prices.get(symbol)}


class _FakePosition:
    def __init__(self, quantity):
        self.quantity = quantity


class _FakeManager:
    def __init__(self, exchange, positions):
        self.exchange = exchange
        self.positions = positions


def test_reconcile_returns_none_in_paper_mode():
    manager = _FakeManager(exchange=None, positions={"BTC/USDT": _FakePosition(1.0)})

    assert reconciliation.reconcile(manager) is None


def test_reconcile_ok_when_balances_match():
    exchange = _FakeExchange({"BTC": 1.0})
    manager = _FakeManager(exchange=exchange, positions={"BTC/USDT": _FakePosition(1.0)})

    result = reconciliation.reconcile(manager)

    assert result.status == "ok"
    assert result.diffs == []


def test_reconcile_detects_mismatch_when_balance_short():
    exchange = _FakeExchange({"BTC": 0.2})
    manager = _FakeManager(exchange=exchange, positions={"BTC/USDT": _FakePosition(1.0)})

    result = reconciliation.reconcile(manager)

    assert result.status == "mismatch"
    assert len(result.diffs) == 1
    assert "BTC/USDT" in result.diffs[0]


def test_reconcile_ok_when_no_local_positions():
    exchange = _FakeExchange({})
    manager = _FakeManager(exchange=exchange, positions={})

    result = reconciliation.reconcile(manager)

    assert result.status == "ok"


def test_reconcile_detects_remote_balance_without_local_position():
    exchange = _FakeExchange({"ETH": 2.0}, prices={"ETH/USDT": 3000.0})
    manager = _FakeManager(exchange=exchange, positions={})

    result = reconciliation.reconcile(manager, tracked_symbols=["ETH/USDT"])

    assert result.status == "mismatch"
    assert "ETH/USDT" in result.diffs[0]


def test_reconcile_ignores_dust_balance_without_local_position():
    exchange = _FakeExchange({"ETH": 0.0001}, prices={"ETH/USDT": 3000.0})
    manager = _FakeManager(exchange=exchange, positions={})

    result = reconciliation.reconcile(manager, tracked_symbols=["ETH/USDT"])

    assert result.status == "ok"


def test_reconcile_ignores_untracked_symbols_without_local_position():
    exchange = _FakeExchange({"BNB": 5.0}, prices={"BNB/USDT": 500.0})
    manager = _FakeManager(exchange=exchange, positions={})

    result = reconciliation.reconcile(manager, tracked_symbols=["ETH/USDT"])

    assert result.status == "ok"


def test_reconcile_treats_untradeable_ticker_as_not_dust():
    exchange = _FakeExchange({"ETH": 0.001}, fail_ticker=True)
    manager = _FakeManager(exchange=exchange, positions={})

    result = reconciliation.reconcile(manager, tracked_symbols=["ETH/USDT"])

    assert result.status == "mismatch"


def test_reconcile_treats_missing_ticker_price_as_not_dust():
    # ticker sem "last" (par ilíquido, sem trade recente) -- nao pode virar
    # dust por omissao, senao uma divergencia real fica escondida.
    exchange = _FakeExchange({"ETH": 0.001}, prices={"ETH/USDT": None})
    manager = _FakeManager(exchange=exchange, positions={})

    result = reconciliation.reconcile(manager, tracked_symbols=["ETH/USDT"])

    assert result.status == "mismatch"


def test_reconcile_never_mutates_local_positions():
    # FR-003: reconciliacao so alerta, nunca corrige o estado local sozinha.
    exchange = _FakeExchange({"BTC": 0.2})
    positions = {"BTC/USDT": _FakePosition(1.0)}
    manager = _FakeManager(exchange=exchange, positions=positions)

    result = reconciliation.reconcile(manager)

    assert result.status == "mismatch"
    assert manager.positions is positions
    assert manager.positions["BTC/USDT"].quantity == 1.0
