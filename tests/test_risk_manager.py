from risk import manager as risk_manager
from risk.manager import calculate_risk


def test_calculate_risk_uses_atr_levels():
    risk = calculate_risk(entry_price=100.0, available_usdt=1000.0, atr=2.0)

    assert risk.quantity == 1.0
    assert risk.stop_loss == 97.0
    assert risk.take_profit == 106.0
    assert risk.risk_usdt == 3.0
    assert risk.atr == 2.0


def test_calculate_risk_caps_stop_loss_at_max_stop_loss_pct(monkeypatch):
    # ATR largo (par de alta volatilidade): ATR_SL_MULTIPLIER puro colocaria o SL a
    # -20% da entrada -- MAX_STOP_LOSS_PCT (8% default) precisa travar antes disso,
    # mesmo caso que motivou a mudanca (ACE/USDT -20.7% de perda real em paper mode).
    monkeypatch.setattr(risk_manager, "MAX_STOP_LOSS_PCT", 0.08)
    risk = calculate_risk(entry_price=100.0, available_usdt=1000.0, atr=13.3)  # SL puro ficaria em ~80 (-20%)

    assert risk.stop_loss == 92.0  # travado em -8%, nao nos -20% que o ATR puro daria


def test_calculate_risk_does_not_cap_stop_loss_when_atr_is_tight(monkeypatch):
    monkeypatch.setattr(risk_manager, "MAX_STOP_LOSS_PCT", 0.08)
    risk = calculate_risk(entry_price=100.0, available_usdt=1000.0, atr=2.0)  # SL puro em 97, dentro do teto de 8%

    assert risk.stop_loss == 97.0


def test_calculate_risk_falls_back_to_percent_levels_without_atr():
    risk = calculate_risk(entry_price=100.0, available_usdt=50.0, atr=0.0)

    assert risk.quantity == 0.475
    assert risk.stop_loss == 98.5
    assert risk.take_profit == 106.0
    assert round(risk.risk_usdt, 6) == 0.7125
