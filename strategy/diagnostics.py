from typing import Optional

from config.settings import HIGH_VOLATILITY_ATR_RATIO, HIGH_VOLATILITY_FILTER_ENABLED
from strategy.base import Signal


def signal_checks(indicators, previous, current_price: float, strategy) -> dict:
    params = strategy.params
    volume_ma = float(indicators.get("volume_ma", 0) or 0)
    volume_ratio = float(indicators.get("volume", 0) or 0) / volume_ma if volume_ma else 0.0
    ema_trend = float(indicators["ema_trend"])
    trend_gap_pct = (current_price - ema_trend) / ema_trend * 100 if ema_trend else 0.0
    atr_pct = float(indicators.get("atr", 0) or 0) / current_price * 100 if current_price else 0.0

    bullish_cross = False
    bearish_cross = False
    if previous is not None:
        bullish_cross = previous["ema_fast"] < previous["ema_slow"] and indicators["ema_fast"] > indicators["ema_slow"]
        bearish_cross = previous["ema_fast"] > previous["ema_slow"] and indicators["ema_fast"] < indicators["ema_slow"]

    trend_aligned = indicators["ema_fast"] > indicators["ema_slow"] > indicators["ema_trend"] and current_price > indicators["ema_trend"]
    pullback_entry = (
        params.pullback_entry_enabled
        and trend_aligned
        and params.pullback_rsi_min <= indicators["rsi"] < params.rsi_overbought
        and indicators.get("low", current_price) <= indicators["ema_slow"] * (1 + params.pullback_max_distance_pct)
        and current_price > indicators["ema_fast"]
        and current_price > indicators.get("open", current_price)
    )

    return {
        "bullish_cross": bullish_cross,
        "bearish_cross": bearish_cross,
        "trend_ok": current_price > indicators["ema_trend"],
        "rsi_ok": indicators["rsi"] < params.rsi_overbought,
        "volume_ok": volume_ratio >= params.volume_min_ratio,
        "bb_ok": current_price <= indicators["bb_upper"],
        "pullback_entry": pullback_entry,
        "volume_ratio": volume_ratio,
        "trend_gap_pct": trend_gap_pct,
        "atr_pct": atr_pct,
    }


def hold_diagnosis(signal, indicators, previous, current_price: float, strategy) -> str:
    if signal.signal == Signal.BUY:
        return "gatilho BUY detectado: validando risco/MTF"
    if signal.signal == Signal.SELL:
        return "gatilho SELL detectado sem posicao aberta"
    if previous is None:
        return "aguardando: historico insuficiente"

    checks_state = signal_checks(indicators, previous, current_price, strategy)
    checks = []

    if not checks_state["bullish_cross"] and not checks_state["pullback_entry"]:
        checks.append("sem cruzamento/pullback")
    if not checks_state["trend_ok"]:
        checks.append("abaixo EMA50")
    if not checks_state["rsi_ok"]:
        checks.append(f"RSI alto {indicators['rsi']:.0f}")
    if not checks_state["volume_ok"]:
        checks.append(f"volume {checks_state['volume_ratio']:.2f}x")
    if not checks_state["bb_ok"]:
        checks.append("acima Bollinger")

    return "aguardando: " + ", ".join(checks[:3]) if checks else "aguardando confirmacao final"


def full_diagnosis(
    indicators, previous, current_price: float, strategy,
    mtf_ok: Optional[bool] = None, cooldown_active: bool = False,
) -> dict:
    """Diagnostico completo (nao truncado) de todas as condicoes de entrada
    de um par -- estende signal_checks() com MTF, regime, volatilidade
    (spec 006) e cooldown, para o modo debug (`python main.py debug <PAR>`).
    Nao duplica a logica de signal_checks(), so adiciona o que falta nele."""
    checks = signal_checks(indicators, previous, current_price, strategy)
    atr_ratio = float(indicators.get("atr_ratio", 0) or 0)
    above_threshold = atr_ratio > HIGH_VOLATILITY_ATR_RATIO
    checks.update({
        "mtf_ok": mtf_ok,
        "regime": indicators.get("regime", "indefinido"),
        "atr_ratio": atr_ratio,
        # so reflete um bloqueio de verdade se o filtro estiver ligado --
        # mostrar True aqui com HIGH_VOLATILITY_FILTER_ENABLED=false
        # induziria o operador a achar que isso esta bloqueando o sinal
        # quando na pratica nao tem efeito nenhum (achado de code-review).
        "high_volatility": HIGH_VOLATILITY_FILTER_ENABLED and above_threshold,
        "cooldown_active": cooldown_active,
    })
    return checks
