from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Sequence

TOLERANCE_PCT = 0.01  # tolerancia para taxas/arredondamento ao comparar saldo real vs esperado
DUST_THRESHOLD_PCT = 0.0001  # ignora saldo residual (fees/rounding) abaixo disso ao checar o sentido inverso


@dataclass
class ReconciliationResult:
    status: str  # "ok" ou "mismatch"
    local_positions: Dict[str, float]
    remote_balances: Dict[str, float]
    diffs: List[str]
    checked_at: datetime = field(default_factory=datetime.now)


def reconcile(manager, tracked_symbols: Optional[Sequence[str]] = None) -> Optional[ReconciliationResult]:
    """Compara posicoes locais (state.json) com o saldo real da conta Binance.

    So roda quando o manager tem uma exchange live conectada (manager.exchange
    is not None); em paper mode nao ha conta real para comparar. Nao corrige
    divergencia automaticamente -- isso e decisao do operador (ver constitution
    P1/P6 e research.md).

    Checa os dois sentidos:
    - posicao local sem saldo real suficiente (ex: venda que falhou "silenciosamente"
      ou state.json desatualizado).
    - saldo real de um par rastreado (`tracked_symbols`) sem posicao local
      correspondente (ex: posicao local perdida por um bug, crash antes de
      persistir, ou edicao manual do state.json). So verificado para pares que
      o bot efetivamente acompanha, para nao alertar sobre outros ativos que o
      operador mantenha na mesma conta por fora do bot.
    """
    if manager.exchange is None:
        return None

    balance = manager.exchange.fetch_balance()
    totals = balance.get("total", {})

    local_positions = {symbol: pos.quantity for symbol, pos in manager.positions.items()}
    remote_balances: Dict[str, float] = {}
    diffs: List[str] = []

    for symbol, expected_qty in local_positions.items():
        base = symbol.split("/")[0]
        actual_qty = float(totals.get(base, 0.0))
        remote_balances[base] = actual_qty
        if actual_qty < expected_qty * (1 - TOLERANCE_PCT):
            diffs.append(
                f"{symbol}: esperado >= {expected_qty:.8f} {base}, "
                f"encontrado {actual_qty:.8f} {base} na conta"
            )

    for symbol in tracked_symbols or []:
        if symbol in local_positions:
            continue
        base = symbol.split("/")[0]
        actual_qty = float(totals.get(base, 0.0))
        if actual_qty <= DUST_THRESHOLD_PCT:
            continue
        remote_balances[base] = actual_qty
        diffs.append(
            f"{symbol}: sem posicao local, mas conta tem {actual_qty:.8f} {base}"
        )

    return ReconciliationResult(
        status="mismatch" if diffs else "ok",
        local_positions=local_positions,
        remote_balances=remote_balances,
        diffs=diffs,
    )
