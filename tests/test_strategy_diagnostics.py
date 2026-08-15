from strategy.diagnostics import full_diagnosis, signal_checks
from strategy.ema_rsi import EmaRsiStrategy


def _indicators(regime="trending", atr_ratio=0.01):
    return {
        "open": 100.0, "high": 101.0, "low": 99.0, "close": 110.0,
        "ema_fast": 12.0, "ema_slow": 10.0, "ema_trend": 95.0,
        "rsi": 55.0, "volume": 150.0, "volume_ma": 100.0, "bb_upper": 120.0,
        "atr": 1.0, "regime": regime, "atr_ratio": atr_ratio,
    }


def test_full_diagnosis_includes_all_signal_checks_fields():
    strategy = EmaRsiStrategy()
    indicators = _indicators()
    base_checks = signal_checks(indicators, None, 110.0, strategy)

    result = full_diagnosis(
        indicators, None, 110.0, strategy,
        mtf_ok=True, cooldown_active=False,
    )

    for key in base_checks:
        assert key in result


def test_full_diagnosis_includes_mtf_regime_volatility_and_cooldown():
    strategy = EmaRsiStrategy()
    indicators = _indicators(regime="sideways", atr_ratio=0.20)

    result = full_diagnosis(
        indicators, None, 110.0, strategy,
        mtf_ok=False, cooldown_active=True,
    )

    assert result["mtf_ok"] is False
    assert result["regime"] == "sideways"
    assert result["high_volatility"] is True
    assert result["cooldown_active"] is True


def test_full_diagnosis_identifies_cooldown_as_blocking_reason():
    # Regressao evitada: cooldown MUST aparecer explicitamente, nao
    # escondido atras de outras condicoes que passariam normalmente.
    strategy = EmaRsiStrategy()
    indicators = _indicators()  # todas as outras condicoes passam

    result = full_diagnosis(
        indicators, None, 110.0, strategy,
        mtf_ok=True, cooldown_active=True,
    )

    assert result["cooldown_active"] is True
