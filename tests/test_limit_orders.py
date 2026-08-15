from execution import order_manager
from execution.order_manager import LIVE_CONFIRMATION_TEXT, OrderManager
from risk.manager import RiskLevels


def _live_manager(monkeypatch, exchange, fetch_balance_fn=lambda: {"USDT": 1000.0}):
    monkeypatch.setattr(order_manager, "TRADING_MODE", "live")
    monkeypatch.setattr(order_manager, "fetch_balance", fetch_balance_fn)
    monkeypatch.setattr(order_manager, "LIVE_TRADING_CONFIRMATION", LIVE_CONFIRMATION_TEXT)
    monkeypatch.setattr(order_manager, "BINANCE_API_KEY", "key")
    monkeypatch.setattr(order_manager, "BINANCE_API_SECRET", "secret")
    monkeypatch.setattr(order_manager, "load_state", lambda: {})
    monkeypatch.setattr(order_manager, "save_state", lambda state: None)
    monkeypatch.setattr(order_manager, "send_telegram", lambda msg: None)
    monkeypatch.setattr(order_manager, "get_exchange", lambda: exchange)
    return OrderManager()


def _risk():
    return RiskLevels(entry_price=100.0, stop_loss=95.0, take_profit=110.0, quantity=1.0, risk_usdt=5.0)


def test_open_long_uses_market_order_when_use_limit_orders_disabled(monkeypatch):
    # USE_LIMIT_ORDERS=false (default) preserva 100% o comportamento a
    # mercado ja validado -- open_long nao deve nem olhar para limit_price.
    monkeypatch.setattr(order_manager, "USE_LIMIT_ORDERS", False)

    class _Exchange:
        def create_market_buy_order(self, symbol, quantity, params=None):
            return {"id": "abc123"}

    manager = _live_manager(monkeypatch, _Exchange())

    manager.open_long("BTC/USDT", _risk(), limit_price=99.5)

    assert manager.has_position("BTC/USDT")
    assert manager.pending_limit_orders == {}


def test_open_long_sends_limit_order_when_enabled_with_limit_price(monkeypatch):
    monkeypatch.setattr(order_manager, "USE_LIMIT_ORDERS", True)
    calls = []

    class _Exchange:
        def create_limit_buy_order(self, symbol, quantity, price, params=None):
            calls.append((symbol, quantity, price, params.get("newClientOrderId")))
            return {"id": "limit-1"}

    manager = _live_manager(monkeypatch, _Exchange())

    manager.open_long("BTC/USDT", _risk(), limit_price=99.5)

    assert len(calls) == 1
    symbol, quantity, price, client_order_id = calls[0]
    assert price == 99.5
    assert client_order_id
    assert not manager.has_position("BTC/USDT")  # so abre posicao quando preenchida
    assert "BTC/USDT" in manager.pending_limit_orders
    assert manager.pending_limit_orders["BTC/USDT"].limit_price == 99.5


def test_open_long_falls_back_to_market_when_limit_price_missing(monkeypatch):
    # USE_LIMIT_ORDERS=true mas sem preco limite disponivel (ex: liquidez
    # nao checada) -- nao pode travar a compra, cai para ordem a mercado.
    monkeypatch.setattr(order_manager, "USE_LIMIT_ORDERS", True)

    class _Exchange:
        def create_market_buy_order(self, symbol, quantity, params=None):
            return {"id": "abc123"}

    manager = _live_manager(monkeypatch, _Exchange())

    manager.open_long("BTC/USDT", _risk(), limit_price=None)

    assert manager.has_position("BTC/USDT")


def _pending_manager(monkeypatch, exchange):
    manager = _live_manager(monkeypatch, exchange)
    manager.pending_limit_orders["BTC/USDT"] = order_manager.PendingLimitOrder(
        symbol="BTC/USDT", client_order_id="bot-limit-1", limit_price=99.5,
        requested_quantity=1.0, stop_loss=95.0, take_profit=110.0, atr=1.0,
    )
    return manager


def test_check_pending_limit_orders_opens_position_on_full_fill(monkeypatch):
    class _Exchange:
        def fetch_order(self, client_order_id, symbol, params=None):
            return {"filled": 1.0, "average": 99.4}

    manager = _pending_manager(monkeypatch, _Exchange())

    manager.check_pending_limit_orders()

    assert "BTC/USDT" not in manager.pending_limit_orders
    assert manager.has_position("BTC/USDT")
    assert manager.get_position("BTC/USDT").quantity == 1.0


def test_check_pending_limit_orders_cancels_and_opens_partial_position_on_timeout(monkeypatch):
    monkeypatch.setattr(order_manager, "LIMIT_ORDER_TIMEOUT_CYCLES", 2)
    cancel_calls = []

    class _Exchange:
        def fetch_order(self, client_order_id, symbol, params=None):
            return {"filled": 0.4, "average": 99.5}

        def cancel_order(self, client_order_id, symbol, params=None):
            cancel_calls.append((client_order_id, symbol))

    manager = _pending_manager(monkeypatch, _Exchange())

    manager.check_pending_limit_orders()  # ciclo 1: ainda dentro do prazo
    assert "BTC/USDT" in manager.pending_limit_orders
    assert not manager.has_position("BTC/USDT")

    manager.check_pending_limit_orders()  # ciclo 2: timeout atingido
    assert "BTC/USDT" not in manager.pending_limit_orders
    assert manager.has_position("BTC/USDT")
    assert manager.get_position("BTC/USDT").quantity == 0.4
    assert len(cancel_calls) == 1


def test_check_pending_limit_orders_cancels_and_discards_on_zero_fill_timeout(monkeypatch):
    monkeypatch.setattr(order_manager, "LIMIT_ORDER_TIMEOUT_CYCLES", 1)
    cancel_calls = []

    class _Exchange:
        def fetch_order(self, client_order_id, symbol, params=None):
            return {"filled": 0.0, "average": None}

        def cancel_order(self, client_order_id, symbol, params=None):
            cancel_calls.append((client_order_id, symbol))

    manager = _pending_manager(monkeypatch, _Exchange())

    manager.check_pending_limit_orders()

    assert "BTC/USDT" not in manager.pending_limit_orders
    assert not manager.has_position("BTC/USDT")
    assert len(cancel_calls) == 1


def test_pending_limit_order_survives_restart_via_persisted_state(monkeypatch):
    saved_states = []
    monkeypatch.setattr(order_manager, "TRADING_MODE", "live")
    monkeypatch.setattr(order_manager, "fetch_balance", lambda: {"USDT": 1000.0})
    monkeypatch.setattr(order_manager, "LIVE_TRADING_CONFIRMATION", LIVE_CONFIRMATION_TEXT)
    monkeypatch.setattr(order_manager, "BINANCE_API_KEY", "key")
    monkeypatch.setattr(order_manager, "BINANCE_API_SECRET", "secret")
    monkeypatch.setattr(order_manager, "load_state", lambda: {})
    monkeypatch.setattr(order_manager, "save_state", lambda state: saved_states.append(state))
    monkeypatch.setattr(order_manager, "send_telegram", lambda msg: None)
    monkeypatch.setattr(order_manager, "USE_LIMIT_ORDERS", True)

    class _Exchange:
        def create_limit_buy_order(self, symbol, quantity, price, params=None):
            return {"id": "limit-1"}

    monkeypatch.setattr(order_manager, "get_exchange", lambda: _Exchange())
    manager = OrderManager()
    manager.open_long("BTC/USDT", _risk(), limit_price=99.5)
    client_order_id = manager.pending_limit_orders["BTC/USDT"].client_order_id

    monkeypatch.setattr(order_manager, "load_state", lambda: saved_states[-1])
    restored = OrderManager()

    assert "BTC/USDT" in restored.pending_limit_orders
    assert restored.pending_limit_orders["BTC/USDT"].client_order_id == client_order_id
