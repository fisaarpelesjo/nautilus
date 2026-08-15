from datetime import datetime

from config.settings import TIMEFRAME
from data.decision_store import log_decision
from strategy.diagnostics import signal_checks


def log_decision_snapshot(cycle_id: int, symbol: str, signal, indicators, previous, current_price: float, row: dict, strategy):
    checks = signal_checks(indicators, previous, current_price, strategy)
    log_decision({
        "timestamp": datetime.now().isoformat(),
        "cycle_id": cycle_id,
        "symbol": symbol,
        "timeframe": TIMEFRAME,
        "price": _round_price(current_price),
        "signal": signal.signal.value,
        "decision": row.get("decision", ""),
        "in_position": row.get("in_pos", False),
        "entry_opened": row.get("entry_opened", False),
        "blockers": row.get("blockers", ""),
        "mtf_checked": row.get("mtf_checked", False),
        "mtf_ok": row.get("mtf_ok", ""),
        "position_pnl_pct": _round_metric(row.get("pnl_pct")),
        "open": _round_price(float(indicators.get("open", current_price))),
        "high": _round_price(float(indicators.get("high", current_price))),
        "low": _round_price(float(indicators.get("low", current_price))),
        "close": _round_price(float(indicators.get("close", current_price))),
        "volume": _round_metric(indicators.get("volume")),
        "ema_fast": _round_price(float(indicators["ema_fast"])),
        "ema_slow": _round_price(float(indicators["ema_slow"])),
        "ema_trend": _round_price(float(indicators["ema_trend"])),
        "rsi": _round_metric(indicators.get("rsi")),
        "macd": _round_metric(indicators.get("macd"), digits=6),
        "atr": _round_price(float(indicators.get("atr", 0) or 0)),
        "atr_pct": _round_metric(checks["atr_pct"]),
        "volume_ma": _round_metric(indicators.get("volume_ma")),
        "volume_ratio": _round_metric(checks["volume_ratio"]),
        "bb_upper": _round_price(float(indicators.get("bb_upper", 0) or 0)),
        "bb_middle": _round_price(float(indicators.get("bb_middle", 0) or 0)),
        "bb_lower": _round_price(float(indicators.get("bb_lower", 0) or 0)),
        "trend_gap_pct": _round_metric(checks["trend_gap_pct"]),
        "bullish_cross": checks["bullish_cross"],
        "bearish_cross": checks["bearish_cross"],
        "trend_ok": checks["trend_ok"],
        "rsi_ok": checks["rsi_ok"],
        "volume_ok": checks["volume_ok"],
        "bb_ok": checks["bb_ok"],
        "pullback_entry": checks["pullback_entry"],
        "regime": indicators.get("regime", ""),
        "reason": signal.reason,
    })


def log_error_decision(cycle_id: int, symbol: str, exc: Exception):
    log_decision({
        "timestamp": datetime.now().isoformat(),
        "cycle_id": cycle_id,
        "symbol": symbol,
        "timeframe": TIMEFRAME,
        "signal": "ERR",
        "decision": f"erro: {str(exc)[:120]}",
        "reason": str(exc),
    })


def _round_price(price: float) -> float:
    if price >= 1:
        return round(price, 4)
    if price >= 0.01:
        return round(price, 6)
    return round(price, 10)


def _round_metric(value, digits: int = 4):
    if value is None or value == "":
        return ""
    return round(float(value), digits)
