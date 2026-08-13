from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Sequence

TOLERANCE_PCT = 0.01  # tolerancia para taxas/arredondamento ao comparar saldo real vs esperado
DUST_THRESHOLD_USDT = 1.0  # abaixo deste valor em USDT, saldo residual nao dispara alerta


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
        actual_qty = float(totals.get(base) or 0.0)
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
        actual_qty = float(totals.get(base) or 0.0)
        if actual_qty <= 0:
            continue
        value_usdt = _estimate_value_usdt(manager, symbol, actual_qty)
        if value_usdt <= DUST_THRESHOLD_USDT:
            continue
        remote_balances[base] = actual_qty
        diffs.append(
            f"{symbol}: sem posicao local, mas conta tem {actual_qty:.8f} {base} "
            f"(~${value_usdt:.2f})"
        )

    return ReconciliationResult(
        status="mismatch" if diffs else "ok",
        local_positions=local_positions,
        remote_balances=remote_balances,
        diffs=diffs,
    )


def _estimate_value_usdt(manager, symbol: str, quantity: float) -> float:
    """Valor aproximado em USDT de `quantity` unidades de `symbol`.

    Se o preco nao puder ser obtido, retorna infinito em vez de 0 -- preferimos
    um falso positivo (alerta por um saldo que pode ser pequeno) a um falso
    negativo (silenciar uma divergencia real so porque o preco falhou).
    """
    try:
        ticker = manager.exchange.fetch_ticker(symbol)
        price = ticker.get("last")
        if not price:
            # Sem preco disponivel (par ilíquido, sem trades recentes) -- nao
            # sabemos o valor real, entao nao pode virar "dust" por omissao.
            return float("inf")
        return quantity * float(price)
    except Exception:
        return float("inf")
