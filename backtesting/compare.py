from dataclasses import dataclass
from typing import Dict, List, Optional
from rich import box
from rich.console import Console
from rich.table import Table
import io
import sys

from backtesting.approval import ApprovalVerdict, evaluate_approval, ranking_key, verdict_markup
from backtesting.engine import run_backtest
from strategy.base import BaseStrategy
from strategy.breakout import BreakoutStrategy
from strategy.ema_rsi import EmaRsiStrategy
from utils.logger import get_logger

log = get_logger("compare")

_stdout_utf8 = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace", line_buffering=True)
# width fixo: mesmo achado ja corrigido em backtesting/multi.py -- sem terminal
# real, Rich cai para ~79 colunas e derruba as ultimas colunas da tabela.
console = Console(file=_stdout_utf8, highlight=False, force_terminal=True, width=150)

DEFAULT_PAIRS = ["BTC/USDT", "ETH/USDT", "SOL/USDT"]
DEFAULT_TIMEFRAME = "4h"

DEFAULT_STRATEGIES: Dict[str, BaseStrategy] = {
    "EMA/RSI padrao": EmaRsiStrategy(),
    "Breakout 150": BreakoutStrategy(window=150),
}


@dataclass
class CompareResult:
    strategy_name: str
    pair: str
    trades: int = 0
    win_rate: float = 0.0
    total_return_pct: float = 0.0
    max_drawdown_pct: float = 0.0
    profit_factor: float = 0.0
    edge_score: float = float("-inf")
    verdict: Optional[ApprovalVerdict] = None
    error: Optional[str] = None


def run_comparison(
    strategies: Dict[str, BaseStrategy], pairs: Optional[List[str]] = None, timeframe: Optional[str] = None,
) -> List[CompareResult]:
    """Roda cada estrategia em cada par, nas mesmas condicoes, e aplica o
    mesmo criterio de veredito ja usado por edge/multibacktest/scan
    (evaluate_approval/edge_score) -- nao inventa um criterio novo de
    comparacao. Funciona normalmente com uma unica estrategia (Edge Case do
    spec.md -- nao exige minimo de itens)."""
    pairs = pairs or DEFAULT_PAIRS
    timeframe = timeframe or DEFAULT_TIMEFRAME
    results: List[CompareResult] = []

    for name, strategy in strategies.items():
        for pair in pairs:
            try:
                result = run_backtest(pair, timeframe, strategy=strategy)
                verdict = evaluate_approval(result)
                results.append(CompareResult(
                    strategy_name=name,
                    pair=pair,
                    trades=result.total_trades,
                    win_rate=result.win_rate,
                    total_return_pct=result.total_return_pct,
                    max_drawdown_pct=result.max_drawdown_pct,
                    profit_factor=result.profit_factor,
                    edge_score=result.edge_score,
                    verdict=verdict,
                ))
            except Exception as exc:
                log.error(f"Erro ao comparar {name} em {pair}: {exc}")
                results.append(CompareResult(strategy_name=name, pair=pair, error=str(exc)))

    results.sort(key=ranking_key, reverse=True)
    return results


def _print_comparison(results: List[CompareResult]):
    table = Table(title="Comparativo de Estrategias/Presets", box=box.ROUNDED, header_style="bold cyan")
    table.add_column("Estrategia")
    table.add_column("Par")
    table.add_column("Trades", justify="right")
    table.add_column("Win rate", justify="right")
    table.add_column("Retorno %", justify="right")
    table.add_column("Drawdown %", justify="right")
    table.add_column("Profit factor", justify="right")
    table.add_column("Edge score", justify="right")
    table.add_column("Veredito")

    for r in results:
        if r.error:
            table.add_row(r.strategy_name, r.pair, "-", "-", "-", "-", "-", "-", f"[red]erro: {r.error[:40]}[/red]")
            continue
        table.add_row(
            r.strategy_name, r.pair, str(r.trades), f"{r.win_rate:.1f}%", f"{r.total_return_pct:+.2f}%",
            f"{r.max_drawdown_pct:.2f}%", f"{r.profit_factor:.2f}", f"{r.edge_score:+.2f}",
            verdict_markup(r.verdict),
        )

    console.print(table)


def run(strategies: Optional[Dict[str, BaseStrategy]] = None, pairs: Optional[List[str]] = None, timeframe: Optional[str] = None):
    results = run_comparison(strategies or DEFAULT_STRATEGIES, pairs, timeframe)
    _print_comparison(results)
    return results
