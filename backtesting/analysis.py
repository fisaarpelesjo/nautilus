import csv
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List

from rich import box
from rich.table import Table

from data.paths import TRADES_FILE
from utils.display import C_DIM, C_LABEL, C_NEG, C_POS, C_PRICE, console, header


@dataclass
class TradeRecord:
    symbol: str
    side: str
    pnl_usdt: float
    pnl_pct: float
    exit_reason: str
    balance_after: float


@dataclass
class AnalysisResult:
    trades: List[TradeRecord]
    total_trades: int
    total_pnl: float
    win_rate: float
    profit_factor: float
    expectancy: float
    average_win: float
    average_loss: float
    largest_win: float
    largest_loss: float
    max_losing_streak: int
    by_symbol: Dict[str, float]
    by_exit_reason: Dict[str, int]
    final_balance: float


def analyze_trades(path: str = TRADES_FILE) -> AnalysisResult:
    trades = _load_trades(path)
    wins = [t.pnl_usdt for t in trades if t.pnl_usdt > 0]
    losses = [t.pnl_usdt for t in trades if t.pnl_usdt < 0]
    total_profit = sum(wins)
    total_loss = abs(sum(losses))
    total_pnl = sum(t.pnl_usdt for t in trades)

    by_symbol = defaultdict(float)
    by_exit_reason = defaultdict(int)
    for trade in trades:
        by_symbol[trade.symbol] += trade.pnl_usdt
        by_exit_reason[trade.exit_reason] += 1

    return AnalysisResult(
        trades=trades,
        total_trades=len(trades),
        total_pnl=total_pnl,
        win_rate=len(wins) / len(trades) * 100 if trades else 0.0,
        profit_factor=total_profit / total_loss if total_loss else (float("inf") if total_profit > 0 else 0.0),
        expectancy=total_pnl / len(trades) if trades else 0.0,
        average_win=total_profit / len(wins) if wins else 0.0,
        average_loss=sum(losses) / len(losses) if losses else 0.0,
        largest_win=max(wins) if wins else 0.0,
        largest_loss=min(losses) if losses else 0.0,
        max_losing_streak=_max_losing_streak(trades),
        by_symbol=dict(sorted(by_symbol.items(), key=lambda item: item[1], reverse=True)),
        by_exit_reason=dict(by_exit_reason),
        final_balance=trades[-1].balance_after if trades else 0.0,
    )


def print_analysis(result: AnalysisResult):
    header()
    console.print(f"  [{C_LABEL}]analise de trades[/{C_LABEL}]")
    console.print()

    if result.total_trades == 0:
        console.print(f"  [{C_DIM}]nenhum trade encontrado em {TRADES_FILE}[/{C_DIM}]")
        console.print()
        return

    pnl_color = C_POS if result.total_pnl >= 0 else C_NEG
    console.print(
        f"  [{C_LABEL}]trades[/{C_LABEL}] [white]{result.total_trades}[/white]"
        f"   [{C_LABEL}]pnl[/{C_LABEL}] [{pnl_color}]{result.total_pnl:+.2f}[/{pnl_color}]"
        f"   [{C_LABEL}]win rate[/{C_LABEL}] [white]{result.win_rate:.1f}%[/white]"
        f"   [{C_LABEL}]profit factor[/{C_LABEL}] [white]{_fmt_metric(result.profit_factor)}[/white]"
    )
    console.print(
        f"  [{C_LABEL}]expectativa[/{C_LABEL}] [white]{result.expectancy:+.2f}/trade[/white]"
        f"   [{C_LABEL}]media win/loss[/{C_LABEL}] [white]{result.average_win:+.2f} / {result.average_loss:+.2f}[/white]"
        f"   [{C_LABEL}]maior win/loss[/{C_LABEL}] [white]{result.largest_win:+.2f} / {result.largest_loss:+.2f}[/white]"
    )
    console.print(f"  [{C_LABEL}]max perdas seguidas[/{C_LABEL}] [white]{result.max_losing_streak}[/white]")
    if result.final_balance:
        console.print(f"  [{C_LABEL}]saldo final registrado[/{C_LABEL}] [{C_PRICE}]${result.final_balance:,.2f}[/{C_PRICE}]")
    console.print()

    _print_symbol_table(result)
    _print_exit_reason_table(result)


def run(path: str = TRADES_FILE):
    print_analysis(analyze_trades(path))


def _load_trades(path: str) -> List[TradeRecord]:
    if not Path(path).exists():
        return []

    with open(path, newline="", encoding="utf-8") as f:
        rows = csv.DictReader(f)
        return [
            TradeRecord(
                symbol=row.get("symbol", ""),
                side=row.get("side", ""),
                pnl_usdt=_to_float(row.get("pnl_usdt")),
                pnl_pct=_to_float(row.get("pnl_pct")),
                exit_reason=row.get("exit_reason", ""),
                balance_after=_to_float(row.get("balance_after")),
            )
            for row in rows
        ]


def _max_losing_streak(trades: List[TradeRecord]) -> int:
    current = 0
    longest = 0
    for trade in trades:
        if trade.pnl_usdt < 0:
            current += 1
            longest = max(longest, current)
        else:
            current = 0
    return longest


def _print_symbol_table(result: AnalysisResult):
    table = Table(box=box.SIMPLE, show_header=True, header_style="bold dim", border_style="dim", pad_edge=False)
    table.add_column("  par", style="white", min_width=14)
    table.add_column("pnl", justify="right", min_width=10)

    for symbol, pnl in result.by_symbol.items():
        color = C_POS if pnl >= 0 else C_NEG
        table.add_row(f"  {symbol}", f"[{color}]{pnl:+.2f}[/{color}]")

    console.print(table)
    console.print()


def _print_exit_reason_table(result: AnalysisResult):
    table = Table(box=box.SIMPLE, show_header=True, header_style="bold dim", border_style="dim", pad_edge=False)
    table.add_column("  motivo de saida", style="white", min_width=18)
    table.add_column("trades", justify="right", min_width=8)

    for reason, count in result.by_exit_reason.items():
        table.add_row(f"  {reason or 'sem motivo'}", str(count))

    console.print(table)
    console.print()


def _to_float(value) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _fmt_metric(value: float) -> str:
    if value == float("inf"):
        return "inf"
    return f"{value:.2f}"
