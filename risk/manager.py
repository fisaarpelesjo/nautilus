from dataclasses import dataclass
from config.settings import STOP_LOSS_PCT, TAKE_PROFIT_PCT, MAX_ORDER_SIZE_USDT, ATR_SL_MULTIPLIER, ATR_TP_MULTIPLIER
from utils.logger import get_logger

log = get_logger("risk")

@dataclass
class RiskLevels:
    entry_price: float
    stop_loss: float
    take_profit: float
    quantity: float
    risk_usdt: float

def calculate_risk(entry_price: float, available_usdt: float, atr: float = 0.0) -> RiskLevels:
    order_size = min(MAX_ORDER_SIZE_USDT, available_usdt * 0.95)
    quantity   = order_size / entry_price

    if atr > 0:
        stop_loss   = entry_price - ATR_SL_MULTIPLIER * atr
        take_profit = entry_price + ATR_TP_MULTIPLIER * atr
        stop_loss   = max(stop_loss, entry_price * 0.5)  # nunca mais de 50% de perda
    else:
        stop_loss   = entry_price * (1 - STOP_LOSS_PCT)
        take_profit = entry_price * (1 + TAKE_PROFIT_PCT)

    risk_usdt = quantity * (entry_price - stop_loss)

    log.info(
        f"Risco calculado | Entrada={entry_price} "
        f"ATR={atr:.6f} SL={stop_loss} TP={take_profit} "
        f"Qtd={quantity:.6f} Risco=${risk_usdt:.2f}"
    )

    return RiskLevels(
        entry_price=entry_price,
        stop_loss=stop_loss,
        take_profit=take_profit,
        quantity=quantity,
        risk_usdt=risk_usdt,
    )

def should_stop_loss(current_price: float, stop_loss: float) -> bool:
    return current_price <= stop_loss

def should_take_profit(current_price: float, take_profit: float) -> bool:
    return current_price >= take_profit
