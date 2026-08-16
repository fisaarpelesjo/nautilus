from dataclasses import dataclass
from typing import List, Optional
from rich.console import Console
from rich.table import Table
from rich import box
import io
import sys

from backtesting.approval import ApprovalVerdict, evaluate_approval, ranking_key, verdict_markup
from backtesting.engine import edge_score_band, run_backtest
from utils.logger import get_logger

log = get_logger("multi_backtest")

_stdout_utf8 = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace", line_buffering=True)
# width fixo: sem terminal real (pipe, log redirecionado, CI), Rich cai para ~79
# colunas e derruba silenciosamente as ultimas colunas da tabela quando elas nao
# cabem -- achado de /code-review high depois que as colunas de edge score/veredito
# empurraram a tabela para alem desse fallback.
console = Console(file=_stdout_utf8, highlight=False, force_terminal=True, width=150)

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
    trades: int = 0
    win_rate: float = 0.0
    retorno_pct: float = 0.0
    drawdown_pct: float = 0.0
    capital_final: float = 0.0
    profit_factor: float = 0.0
    buy_hold_return_pct: float = 0.0
    edge_score: float = float("-inf")
    verdict: Optional[ApprovalVerdict] = None
    error: Optional[str] = None

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
                        pair                = pair,
                        timeframe           = tf,
                        periodo             = periodo,
                        trades              = r.total_trades,
                        win_rate            = r.win_rate,
                        retorno_pct         = r.total_return_pct,
                        drawdown_pct        = r.max_drawdown_pct,
                        capital_final       = r.final_capital,
                        profit_factor       = r.profit_factor,
                        buy_hold_return_pct = r.buy_hold_return_pct,
                        edge_score          = r.edge_score,
                        verdict             = evaluate_approval(r),
                    ))
                except Exception as e:
                    log.error(f"{pair} {tf}: {e}")
                    results.append(MultiResult(pair=pair, timeframe=tf, periodo=periodo, error=str(e)))

    # ranking_key (backtesting/approval.py) trata edge_score desc, desempate por
    # profit_factor/trades e amostra minuscula -- compartilhado com scanner.py.
    # Linhas de erro ficam por ultimo dentro de cada timeframe, ja que
    # print_results() filtra por timeframe preservando a ordem relativa (sort
    # estavel).
    results.sort(key=ranking_key, reverse=True)
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
        table.add_column("edge score", justify="right", min_width=14)
        table.add_column("veredito", justify="right", min_width=12)

        for r in tf_results:
            if r.error:
                table.add_row(f"  {r.pair}", "-", "-", "-", "-", "-", "-", f"[bright_red]erro: {r.error}[/bright_red]")
                continue

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
                f"{r.edge_score:+.1f} {edge_score_band(r.edge_score)}",
                verdict_markup(r.verdict),
            )

        console.print(table)

    _print_summary(results)

def _print_summary(results: List[MultiResult]):
    console.print("  [dim]" + "─" * 70 + "[/dim]")
    console.print()

    valid = [r for r in results if r.error is None]
    if not valid:
        console.print("  [dim]nenhum resultado valido (todos os pares falharam)[/dim]")
        console.print()
        return

    positivos = [r for r in valid if r.retorno_pct > 0]
    melhor    = max(valid, key=lambda r: r.retorno_pct)
    pior      = min(valid, key=lambda r: r.retorno_pct)

    console.print(f"  [dim]resultados positivos[/dim]  [bright_green]{len(positivos)}/{len(valid)}[/bright_green]")
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
    return results
