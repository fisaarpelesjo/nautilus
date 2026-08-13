import pytest

from execution import order_manager
from execution.order_manager import LIVE_CONFIRMATION_TEXT, OrderManager
from risk.manager import RiskLevels


def test_order_manager_does_not_initialize_exchange_in_paper(monkeypatch):
    monkeypatch.setattr(order_manager, "TRADING_MODE", "paper")
    monkeypatch.setattr(order_manager, "load_state", lambda: {})
    monkeypatch.setattr(
        order_manager,
        "get_exchange",
        lambda: pytest.fail("paper mode must not initialize live exchange"),
    )

    manager = OrderManager()

    assert manager.exchange is None


def test_live_mode_requires_explicit_confirmation(monkeypatch):
    monkeypatch.setattr(order_manager, "TRADING_MODE", "live")
    monkeypatch.setattr(order_manager, "LIVE_TRADING_CONFIRMATION", "")
    monkeypatch.setattr(order_manager, "BINANCE_API_KEY", "key")
    monkeypatch.setattr(order_manager, "BINANCE_API_SECRET", "secret")
    monkeypatch.setattr(order_manager, "load_state", lambda: {})

    with pytest.raises(RuntimeError, match="Live trading bloqueado"):
        OrderManager()


def test_live_mode_requires_api_credentials(monkeypatch):
    monkeypatch.setattr(order_manager, "TRADING_MODE", "live")
    monkeypatch.setattr(order_manager, "LIVE_TRADING_CONFIRMATION", LIVE_CONFIRMATION_TEXT)
    monkeypatch.setattr(order_manager, "BINANCE_API_KEY", "")
    monkeypatch.setattr(order_manager, "BINANCE_API_SECRET", "")
    monkeypatch.setattr(order_manager, "load_state", lambda: {})

    with pytest.raises(RuntimeError, match="BINANCE_API_KEY"):
        OrderManager()


def test_generate_client_order_id_is_unique():
    ids = {order_manager._generate_client_order_id() for _ in range(200)}

    assert len(ids) == 200


def _paper_manager(monkeypatch, logged_trades=None):
    monkeypatch.setattr(order_manager, "TRADING_MODE", "paper")
    monkeypatch.setattr(order_manager, "load_state", lambda: {})
    monkeypatch.setattr(order_manager, "save_state", lambda state: None)
    monkeypatch.setattr(order_manager, "send_telegram", lambda msg: None)
    if logged_trades is not None:
        monkeypatch.setattr(order_manager, "log_trade", lambda trade: logged_trades.append(trade))
    return OrderManager()


def test_paper_buy_assigns_unique_client_order_id(monkeypatch):
    manager = _paper_manager(monkeypatch)
    risk = RiskLevels(entry_price=100.0, stop_loss=95.0, take_profit=110.0, quantity=1.0, risk_usdt=5.0)

    manager.open_long("BTC/USDT", risk)

    pos = manager.get_position("BTC/USDT")
    assert pos.client_order_id
    assert pos.client_order_id.startswith("bot-")


def test_paper_sell_persists_client_order_id_on_trade(monkeypatch):
    logged_trades = []
    manager = _paper_manager(monkeypatch, logged_trades)
    risk = RiskLevels(entry_price=100.0, stop_loss=95.0, take_profit=110.0, quantity=1.0, risk_usdt=5.0)
    manager.open_long("BTC/USDT", risk)
    client_order_id = manager.get_position("BTC/USDT").client_order_id

    manager.close_position("BTC/USDT", "take_profit", current_price=110.0)

    assert logged_trades[0]["client_order_id"] == client_order_id


def test_record_reconciliation_persists_and_is_restored(monkeypatch):
    saved_states = []
    monkeypatch.setattr(order_manager, "TRADING_MODE", "paper")
    monkeypatch.setattr(order_manager, "load_state", lambda: {})
    monkeypatch.setattr(order_manager, "save_state", lambda state: saved_states.append(state))

    manager = OrderManager()
    manager.record_reconciliation("mismatch", "2026-08-13T00:00:00", ["BTC/USDT: divergente"])

    assert manager.last_reconciliation["status"] == "mismatch"
    assert saved_states[-1]["last_reconciliation"]["status"] == "mismatch"

    monkeypatch.setattr(order_manager, "load_state", lambda: saved_states[-1])
    restored = OrderManager()
    assert restored.last_reconciliation["status"] == "mismatch"


def test_live_sell_keeps_local_position_when_exchange_call_fails(monkeypatch):
    class _FailingExchange:
        def create_market_sell_order(self, symbol, quantity, params=None):
            raise RuntimeError("network timeout")

    monkeypatch.setattr(order_manager, "TRADING_MODE", "live")
    monkeypatch.setattr(order_manager, "LIVE_TRADING_CONFIRMATION", LIVE_CONFIRMATION_TEXT)
    monkeypatch.setattr(order_manager, "BINANCE_API_KEY", "key")
    monkeypatch.setattr(order_manager, "BINANCE_API_SECRET", "secret")
    monkeypatch.setattr(order_manager, "load_state", lambda: {})
    monkeypatch.setattr(order_manager, "save_state", lambda state: None)
    monkeypatch.setattr(order_manager, "send_telegram", lambda msg: None)
    monkeypatch.setattr(order_manager, "get_exchange", lambda: _FailingExchange())

    manager = OrderManager()
    manager.positions["BTC/USDT"] = order_manager.Position(
        symbol="BTC/USDT", side="long", entry_price=100.0, quantity=1.0,
        stop_loss=95.0, take_profit=110.0,
    )

    manager.close_position("BTC/USDT", "stop_loss")

    assert manager.has_position("BTC/USDT")
