from dataclasses import dataclass
from typing import List
from rich.console import Console
from rich.table import Table
from rich import box
import io
import sys

from backtesting.engine import run_backtest
from utils.logger import get_logger

log = get_logger("multi_backtest")

_stdout_utf8 = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace", line_buffering=True)
console = Console(file=_stdout_utf8, highlight=False, force_terminal=True)

PAIRS = [
    "BTC/USDT",
    "ETH/USDT",
    "SOL/USDT",
    "BNB/USDT",
    "XRP/USDT",
]

TIMEFRAMES = [
    ("1d",  365,  "1 ano"),
    ("4h",  2000, "~333 dias"),
    ("1h",  1000, "~41 dias"),
]

@dataclass
class MultiResult:
    pair: str
    timeframe: str
    periodo: str
    trades: int
    win_rate: float
    retorno_pct: float
    drawdown_pct: float
    capital_final: float

def run_all(initial_capital: float = 1000.0) -> List[MultiResult]:
    results: List[MultiResult] = []

    total = len(PAIRS) * len(TIMEFRAMES)
    done  = 0

    for tf, limit, periodo in TIMEFRAMES:
        for pair in PAIRS:
            done += 1
            with console.status(
                f"  [dim cyan]testando {pair} {tf}... ({done}/{total})[/dim cyan]",
                spinner="dots", spinner_style="cyan"
            ):
                try:
                    r = run_backtest(pair, tf, initial_capital, candle_limit=limit)
                    results.append(MultiResult(
                        pair          = pair,
                        timeframe     = tf,
                        periodo       = periodo,
                        trades        = r.total_trades,
                        win_rate      = r.win_rate,
                        retorno_pct   = r.total_return_pct,
                        drawdown_pct  = r.max_drawdown_pct,
                        capital_final = r.final_capital,
                    ))
                except Exception as e:
                    log.error(f"{pair} {tf}: {e}")

    return results

def print_results(results: List[MultiResult]):
    console.print()
    console.print("  [bold cyan]◆[/bold cyan] [bold white]multi backtest[/bold white]  [dim cyan]EMA 9/21/50 · SL 1.5% · TP 6%[/dim cyan]")
    console.print("  [dim]" + "─" * 70 + "[/dim]")
    console.print()

    for tf, _, periodo in TIMEFRAMES:
        tf_results = [r for r in results if r.timeframe == tf]
        if not tf_results:
            continue

        table = Table(
            box=box.SIMPLE,
            show_header=True,
            header_style="bold dim",
            border_style="dim",
            pad_edge=False,
        )
        table.add_column(f"  {tf} · {periodo}", style="white", min_width=12)
        table.add_column("trades",   justify="right", min_width=7)
        table.add_column("win rate", justify="right", min_width=9)
        table.add_column("retorno",  justify="right", min_width=9)
        table.add_column("drawdown", justify="right", min_width=10)
        table.add_column("capital",  justify="right", min_width=10)

        for r in tf_results:
            ret_color = "bright_green" if r.retorno_pct > 0 else "bright_red"
            wr_color  = "bright_green" if r.win_rate >= 50 else "red"
            dd_color  = "bright_red" if r.drawdown_pct > 10 else "yellow" if r.drawdown_pct > 5 else "green"

            table.add_row(
                f"  {r.pair}",
                str(r.trades),
                f"[{wr_color}]{r.win_rate:.1f}%[/{wr_color}]",
                f"[{ret_color}]{r.retorno_pct:+.2f}%[/{ret_color}]",
                f"[{dd_color}]{r.drawdown_pct:.2f}%[/{dd_color}]",
                f"${r.capital_final:.2f}",
            )

        console.print(table)

    _print_summary(results)

def _print_summary(results: List[MultiResult]):
    console.print("  [dim]" + "─" * 70 + "[/dim]")
    console.print()

    positivos = [r for r in results if r.retorno_pct > 0]
    melhor    = max(results, key=lambda r: r.retorno_pct)
    pior      = min(results, key=lambda r: r.retorno_pct)

    console.print(f"  [dim]resultados positivos[/dim]  [bright_green]{len(positivos)}/{len(results)}[/bright_green]")
    console.print(
        f"  [dim]melhor[/dim]  [bright_green]{melhor.pair} {melhor.timeframe} "
        f"{melhor.retorno_pct:+.2f}%[/bright_green]"
    )
    console.print(
        f"  [dim]pior  [/dim]  [bright_red]{pior.pair} {pior.timeframe} "
        f"{pior.retorno_pct:+.2f}%[/bright_red]"
    )
    console.print()

def run():
    results = run_all()
    print_results(results)
