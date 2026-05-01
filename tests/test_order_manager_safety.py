import pytest

from execution import order_manager
from execution.order_manager import LIVE_CONFIRMATION_TEXT, OrderManager


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
