from data.decisions_analysis import analyze_decisions
from data.signal_store import load_recent_signals
from data.trade_store import load_recent_trades
from execution.order_manager import OrderManager
from trading.portfolio import compute_portfolio_snapshot
from utils.display import C_CYAN, C_DIM, console, header, print_portfolio_summary


def print_panel(manager: OrderManager):
    """Agrega patrimonio, posicoes, ultimas operacoes, ultimos sinais e
    bloqueios recentes numa unica execucao -- so leitura, nenhuma secao
    lanca excecao com historico ausente/vazio (FR-005)."""
    header()
    console.print(f"[bold {C_CYAN}]painel operacional[/bold {C_CYAN}]")
    console.print()

    snap = compute_portfolio_snapshot(manager)
    print_portfolio_summary(snap)
    console.print()

    console.print(f"[bold {C_CYAN}]posições abertas[/bold {C_CYAN}]")
    if manager.positions:
        for symbol, pos in manager.positions.items():
            console.print(f"  [{C_CYAN}]{symbol}[/{C_CYAN}]  entrada ${pos.entry_price:.4f}  qtd {pos.quantity}")
    else:
        console.print(f"  [{C_DIM}]nenhuma posição aberta[/{C_DIM}]")
    console.print()

    console.print(f"[bold {C_CYAN}]últimas operações[/bold {C_CYAN}]")
    trades = load_recent_trades(n=10)
    if trades:
        for t in trades:
            pnl = t.get("pnl_usdt", "")
            console.print(f"  [{C_DIM}]{t.get('closed_at', '')}[/{C_DIM}]  {t.get('symbol', '')}  {t.get('exit_reason', '')}  pnl ${pnl}")
    else:
        console.print(f"  [{C_DIM}]nenhuma operação ainda[/{C_DIM}]")
    console.print()

    console.print(f"[bold {C_CYAN}]últimos sinais[/bold {C_CYAN}]")
    signals = load_recent_signals(n=10)
    if signals:
        for s in signals:
            console.print(f"  [{C_DIM}]{s.get('timestamp', '')}[/{C_DIM}]  {s.get('symbol', '')}  {s.get('signal', '')}")
    else:
        console.print(f"  [{C_DIM}]nenhum sinal registrado ainda[/{C_DIM}]")
    console.print()

    console.print(f"[bold {C_CYAN}]bloqueios recentes[/bold {C_CYAN}]")
    decisions = analyze_decisions()
    if decisions.status == "ok" and decisions.blocker_counts:
        for blocker, count in decisions.blocker_counts[:5]:
            console.print(f"  [{C_DIM}]{blocker}[/{C_DIM}]  {count}x")
    else:
        console.print(f"  [{C_DIM}]nenhum bloqueio registrado ainda[/{C_DIM}]")
