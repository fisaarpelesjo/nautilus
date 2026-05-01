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


def test_validate_config_requires_confirmation_for_live(monkeypatch):
    monkeypatch.setattr(settings, "TRADING_MODE", "live")
    monkeypatch.setattr(settings, "LIVE_TRADING_CONFIRMATION", "")
    monkeypatch.setattr(settings, "BINANCE_API_KEY", "key")
    monkeypatch.setattr(settings, "BINANCE_API_SECRET", "secret")

    with pytest.raises(ValueError, match="LIVE_TRADING_CONFIRMATION"):
        settings.validate_config()
