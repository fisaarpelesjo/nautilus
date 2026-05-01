from rich import box
from rich.table import Table

from market.selector import select_dynamic_pairs
from utils.display import C_NEG, C_POS, console, header


def run():
    header()
    results = select_dynamic_pairs()
    _print_results(results)


def _print_results(results):
    if not results:
        console.print("  [dim]nenhum par aprovado pelos filtros dinamicos[/dim]")
        console.print()
        return

    table = Table(box=box.SIMPLE, show_header=True, header_style="bold dim", border_style="dim", pad_edge=False)
    table.add_column("  par", style="white", min_width=14)
    table.add_column("volume 24h", justify="right", min_width=12)
    table.add_column("spread", justify="right", min_width=8)
    table.add_column("volatilidade", justify="right", min_width=12)
    table.add_column("tendencia", justify="right", min_width=10)
    table.add_column("backtest", justify="right", min_width=10)
    table.add_column("trades", justify="right", min_width=7)
    table.add_column("score", justify="right", min_width=8)

    for item in results:
        trend_color = C_POS if item.trend_pct >= 0 else C_NEG
        bt_color = C_POS if item.backtest_return_pct >= 0 else C_NEG
        table.add_row(
            f"  {item.symbol}",
            f"${item.volume_24h / 1_000_000:.1f}M",
            f"{item.spread_pct * 100:.2f}%",
            f"{item.volatility_pct:.2f}%",
            f"[{trend_color}]{item.trend_pct:+.2f}%[/{trend_color}]",
            f"[{bt_color}]{item.backtest_return_pct:+.2f}%[/{bt_color}]",
            str(item.backtest_trades),
            f"{item.score:.2f}",
        )

    console.print(table)
    console.print()
