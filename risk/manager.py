from dataclasses import dataclass
from config.settings import STOP_LOSS_PCT, TAKE_PROFIT_PCT, MAX_ORDER_SIZE_USDT
from utils.logger import get_logger

log = get_logger("risk")

@dataclass
class RiskLevels:
    entry_price: float
    stop_loss: float
    take_profit: float
    quantity: float
    risk_usdt: float

def calculate_risk(entry_price: float, available_usdt: float) -> RiskLevels:
    order_size = min(MAX_ORDER_SIZE_USDT, available_usdt * 0.95)
    quantity = order_size / entry_price

    stop_loss = entry_price * (1 - STOP_LOSS_PCT)
    take_profit = entry_price * (1 + TAKE_PROFIT_PCT)
    risk_usdt = quantity * (entry_price - stop_loss)

    log.info(
        f"Risco calculado | Entrada={entry_price:.2f} "
        f"SL={stop_loss:.2f} TP={take_profit:.2f} "
        f"Qtd={quantity:.6f} Risco=${risk_usdt:.2f}"
    )

    return RiskLevels(
        entry_price=entry_price,
        stop_loss=stop_loss,
        take_profit=take_profit,
        quantity=quantity,
        risk_usdt=risk_usdt,
    )

def should_stop_loss(current_price: float, entry_price: float) -> bool:
    return current_price <= entry_price * (1 - STOP_LOSS_PCT)

def should_take_profit(current_price: float, entry_price: float) -> bool:
    return current_price >= entry_price * (1 + TAKE_PROFIT_PCT)
