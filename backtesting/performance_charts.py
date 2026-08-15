from dataclasses import dataclass
from typing import List, Optional

import plotly.graph_objects as go


@dataclass
class PerformanceFigures:
    status: str  # "ok" | "sem_dados"
    capital_curve: Optional[go.Figure] = None
    drawdown_curve: Optional[go.Figure] = None
    pnl_by_pair: Optional[go.Figure] = None


def build_performance_figures(trades: List[dict]) -> PerformanceFigures:
    """Curva de capital, drawdown e PnL por par a partir de linhas de
    data/trades.csv (ou equivalente). Lista vazia/ausente vira estado
    explicito "sem_dados", nunca erro (FR-005)."""
    if not trades:
        return PerformanceFigures(status="sem_dados")

    closed_at = [t.get("closed_at", "") for t in trades]
    balances = [float(t.get("balance_after") or 0.0) for t in trades]
    pnls = [float(t.get("pnl_usdt") or 0.0) for t in trades]
    symbols = [t.get("symbol", "") for t in trades]

    capital_fig = go.Figure()
    capital_fig.add_trace(go.Scatter(x=closed_at, y=balances, mode="lines+markers", name="capital"))
    capital_fig.update_layout(title="Curva de capital", xaxis_title="fechamento", yaxis_title="saldo (USDT)")

    peak = balances[0]
    drawdowns = []
    for b in balances:
        peak = max(peak, b)
        drawdowns.append((peak - b) / peak * 100 if peak else 0.0)
    drawdown_fig = go.Figure()
    drawdown_fig.add_trace(go.Scatter(x=closed_at, y=drawdowns, mode="lines", name="drawdown", fill="tozeroy"))
    drawdown_fig.update_layout(title="Drawdown ao longo do tempo", xaxis_title="fechamento", yaxis_title="drawdown (%)")

    pnl_per_symbol: dict = {}
    for symbol, pnl in zip(symbols, pnls, strict=True):
        pnl_per_symbol[symbol] = pnl_per_symbol.get(symbol, 0.0) + pnl
    pnl_fig = go.Figure()
    pnl_fig.add_trace(go.Bar(x=list(pnl_per_symbol.keys()), y=list(pnl_per_symbol.values()), name="pnl por par"))
    pnl_fig.update_layout(title="PnL por par", xaxis_title="par", yaxis_title="PnL (USDT)")

    return PerformanceFigures(status="ok", capital_curve=capital_fig, drawdown_curve=drawdown_fig, pnl_by_pair=pnl_fig)
