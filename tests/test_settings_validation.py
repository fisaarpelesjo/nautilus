import pytest

from config import settings


def test_validate_config_accepts_current_defaults():
    settings.validate_config()


def test_validate_config_rejects_invalid_trading_mode(monkeypatch):
    monkeypatch.setattr(settings, "TRADING_MODE", "demo")

    with pytest.raises(ValueError, match="TRADING_MODE"):
        settings.validate_config()


def test_validate_config_rejects_invalid_pair(monkeypatch):
    monkeypatch.setattr(settings, "PAIRS", ["BTCUSDT"])

    with pytest.raises(ValueError, match="PAIRS invalidos"):
        settings.validate_config()


def test_validate_config_rejects_max_consecutive_losses_below_one(monkeypatch):
    monkeypatch.setattr(settings, "MAX_CONSECUTIVE_LOSSES", 0)

    with pytest.raises(ValueError, match="MAX_CONSECUTIVE_LOSSES"):
        settings.validate_config()


def test_validate_config_rejects_edge_min_trades_below_one(monkeypatch):
    monkeypatch.setattr(settings, "EDGE_MIN_TRADES", 0)

    with pytest.raises(ValueError, match="EDGE_MIN_TRADES"):
        settings.validate_config()


def test_validate_config_rejects_weekly_limit_below_daily(monkeypatch):
    monkeypatch.setattr(settings, "DAILY_DRAWDOWN_LIMIT", 0.10)
    monkeypatch.setattr(settings, "WEEKLY_DRAWDOWN_LIMIT", 0.05)

    with pytest.raises(ValueError, match="WEEKLY_DRAWDOWN_LIMIT"):
        settings.validate_config()


def test_validate_config_rejects_monthly_limit_below_weekly(monkeypatch):
    monkeypatch.setattr(settings, "WEEKLY_DRAWDOWN_LIMIT", 0.10)
    monkeypatch.setattr(settings, "MONTHLY_DRAWDOWN_LIMIT", 0.05)

    with pytest.raises(ValueError, match="MONTHLY_DRAWDOWN_LIMIT"):
        settings.validate_config()


def test_validate_config_requires_confirmation_for_live(monkeypatch):
    monkeypatch.setattr(settings, "TRADING_MODE", "live")
    monkeypatch.setattr(settings, "LIVE_TRADING_CONFIRMATION", "")
    monkeypatch.setattr(settings, "BINANCE_API_KEY", "key")
    monkeypatch.setattr(settings, "BINANCE_API_SECRET", "secret")

    with pytest.raises(ValueError, match="LIVE_TRADING_CONFIRMATION"):
        settings.validate_config()
