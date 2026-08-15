from dataclasses import dataclass, field
from typing import List, Optional

from config.settings import TRADING_MODE
from data.fetcher import fetch_balance, fetch_ticker
from execution.order_manager import OrderManager


@dataclass
class PortfolioSnapshot:
    free_cash: float
    positions_value: Optional[float]
    total_equity: Optional[float]
    realized_pnl: float
    unrealized_pnl: Optional[float]
    total_pnl: Optional[float]
    positions_with_unknown_price: List[str] = field(default_factory=list)


def _current_free_cash(manager: OrderManager) -> Optional[float]:
    """Mesma bifurcacao paper/live ja usada em
    trading/position_lifecycle.py _current_balance e
    execution/order_manager.py _reference_balance -- saldo desconhecido
    (falha ao buscar em live) MUST virar None, nunca 0.0 silencioso."""
    if TRADING_MODE == "paper":
        return manager.paper_balance_usdt
    try:
        balance = fetch_balance()
        return float(balance.get("USDT", 0))
    except Exception:
        return None


def compute_portfolio_snapshot(manager: OrderManager) -> PortfolioSnapshot:
    """Caixa livre, valor em posicoes, patrimonio total e os 3 PnLs --
    calculo centralizado, reusado por status e painel (US1/US3). Preco
    indisponivel para uma posicao propaga None em todos os campos
    agregados (positions_value/total_equity/unrealized_pnl/total_pnl),
    nunca 0.0 silencioso -- mesmo principio ja usado para saldo
    desconhecido em handle_entry_candidate."""
    free_cash = _current_free_cash(manager)

    positions_value = 0.0
    unrealized_pnl = 0.0
    unknown: List[str] = []

    for symbol, pos in manager.positions.items():
        try:
            current_price = float(fetch_ticker(symbol)["last"])
        except Exception:
            unknown.append(symbol)
            continue
        positions_value += pos.quantity * current_price
        unrealized_pnl += (current_price - pos.entry_price) * pos.quantity

    if unknown:
        positions_value = None
        unrealized_pnl = None

    total_equity = (free_cash + positions_value) if (free_cash is not None and positions_value is not None) else None
    total_pnl = (manager.realized_pnl + unrealized_pnl) if unrealized_pnl is not None else None

    return PortfolioSnapshot(
        free_cash=free_cash,
        positions_value=positions_value,
        total_equity=total_equity,
        realized_pnl=manager.realized_pnl,
        unrealized_pnl=unrealized_pnl,
        total_pnl=total_pnl,
        positions_with_unknown_price=unknown,
    )
