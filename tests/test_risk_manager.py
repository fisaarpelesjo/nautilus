from risk.manager import calculate_risk


def test_calculate_risk_uses_atr_levels():
    risk = calculate_risk(entry_price=100.0, available_usdt=1000.0, atr=2.0)

    assert risk.quantity == 1.0
    assert risk.stop_loss == 97.0
    assert risk.take_profit == 106.0
    assert risk.risk_usdt == 3.0
    assert risk.atr == 2.0


def test_calculate_risk_falls_back_to_percent_levels_without_atr():
    risk = calculate_risk(entry_price=100.0, available_usdt=50.0, atr=0.0)

    assert risk.quantity == 0.475
    assert risk.stop_loss == 98.5
    assert risk.take_profit == 106.0
    assert round(risk.risk_usdt, 6) == 0.7125
