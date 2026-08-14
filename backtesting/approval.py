from dataclasses import dataclass
from typing import List, Optional

from backtesting.engine import BacktestResult
from config.settings import EDGE_MIN_TRADES

# Criterios de aprovacao automatica (ROADMAP.md, esbocado na Fase 1), aplicaveis a
# qualquer resultado de backtest de janela unica -- com ou sem split treino/validacao
# (spec 001 US3 usa isto sobre a janela de validacao; spec 002 usa isto direto sobre
# o resultado de edge/multibacktest/scan, que nunca fazem split).
MIN_PROFIT_FACTOR_FOR_APPROVAL = 1.2
MAX_ACCEPTABLE_DRAWDOWN_PCT = 10.0


@dataclass
class ApprovalVerdict:
    status: str  # "aprovado" | "reprovado" | "inconclusivo"
    reasons: List[str]


def evaluate_approval(
    result: Optional[BacktestResult],
    min_trades: int = EDGE_MIN_TRADES,
    min_profit_factor: float = MIN_PROFIT_FACTOR_FOR_APPROVAL,
    max_drawdown_pct: float = MAX_ACCEPTABLE_DRAWDOWN_PCT,
) -> ApprovalVerdict:
    """Aplica os criterios de aprovacao automatica sobre um resultado de backtest
    de janela unica (nunca sobre a janela de treino, quando houver split -- ver
    backtesting/validation.py)."""
    if result is None:
        return ApprovalVerdict(
            status="inconclusivo",
            reasons=["dados insuficientes para uma janela de validacao out-of-sample"],
        )

    reasons: List[str] = []
    if result.total_trades < min_trades:
        reasons.append(f"apenas {result.total_trades} trades na validacao (minimo {min_trades})")
    if result.total_return_pct <= result.buy_hold_return_pct:
        reasons.append(
            f"retorno {result.total_return_pct:+.2f}% nao supera buy-and-hold "
            f"{result.buy_hold_return_pct:+.2f}%"
        )
    if result.profit_factor <= min_profit_factor:
        reasons.append(f"profit factor {result.profit_factor:.2f} abaixo do minimo {min_profit_factor}")
    if result.max_drawdown_pct > max_drawdown_pct:
        reasons.append(f"drawdown {result.max_drawdown_pct:.2f}% acima do aceitavel {max_drawdown_pct:.0f}%")

    if reasons:
        return ApprovalVerdict(status="reprovado", reasons=reasons)
    return ApprovalVerdict(status="aprovado", reasons=[])
