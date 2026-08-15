import io
import sys
from contextlib import contextmanager
from datetime import datetime

from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.rule import Rule
from rich.table import Table

_out = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace", line_buffering=True)
# width fixo: sem terminal real (pipe, log redirecionado, CI), Rich cai para ~79
# colunas e derruba silenciosamente as ultimas colunas de tabelas largas (achado de
# /code-review high na spec 002, mesma causa raiz aqui no console compartilhado
# usado por optimizer.py/engine.py/validation.py/robustness.py).
console = Console(file=_out, highlight=False, force_terminal=True, width=150)

C_DIAMOND = "bold cyan"
C_PIPE = "dim"
C_OK = "bold bright_green"
C_FAIL = "bold bright_red"
C_WARN = "bold yellow"
C_PRICE = "bold white"
C_LABEL = "dim"
C_DIM = "dim"
C_BUY = "bold bright_green"
C_SELL = "bold bright_red"
C_HOLD = "dim"
C_CYAN = "cyan"
C_RSI_OK = "white"
C_RSI_HOT = "bright_red"
C_RSI_COLD = "bright_green"
C_POS = "bright_green"
C_NEG = "bright_red"
C_PANEL = "cyan"


def _d(txt): return f"[{C_DIAMOND}]◆[/{C_DIAMOND}]  {txt}"
def _p(txt): return f"[{C_PIPE}]│[/{C_PIPE}]  {txt}"
def _ok(txt): return f"[{C_OK}]✓[/{C_OK}]  {txt}"
def _err(txt): return f"[{C_FAIL}]✗[/{C_FAIL}]  {txt}"


def _fmt_price(price: float) -> str:
    if price == 0:
        return "$0"
    if price >= 1000:
        return f"${price:,.2f}"
    if price >= 1:
        return f"${price:,.4f}"
    if price >= 0.01:
        return f"${price:.6f}"
    return f"${price:.8f}"


def _fmt_num(value: float) -> str:
    if value == 0:
        return "0"
    if value >= 1000:
        return f"{value:,.2f}"
    if value >= 1:
        return f"{value:,.4f}"
    if value >= 0.01:
        return f"{value:.6f}"
    return f"{value:.8f}"


def _rsi_color(rsi):
    from config.settings import RSI_OVERBOUGHT, RSI_OVERSOLD
    if rsi > RSI_OVERBOUGHT:
        return C_RSI_HOT
    if rsi < RSI_OVERSOLD:
        return C_RSI_COLD
    return C_RSI_OK


def _pnl_color(value):
    return C_POS if value >= 0 else C_NEG


def _pct_color(value: float, positive_good: bool = True):
    if value == 0:
        return C_DIM
    good = value > 0 if positive_good else value < 0
    return C_POS if good else C_NEG


def header():
    from config.settings import DYNAMIC_PAIRS_ENABLED, SYMBOL, TIMEFRAME, TRADING_MODE

    mode_color = C_WARN if TRADING_MODE == "live" else C_CYAN
    pair_mode = "dinamico" if DYNAMIC_PAIRS_ENABLED else "fixo"
    console.print()
    console.print(Panel.fit(
        f"[bold white]crypto trader[/bold white]\n"
        f"[{C_LABEL}]par base[/] [{C_PRICE}]{SYMBOL}[/]   "
        f"[{C_LABEL}]timeframe[/] [{C_CYAN}]{TIMEFRAME}[/]   "
        f"[{C_LABEL}]modo[/] [{mode_color}]{TRADING_MODE}[/]   "
        f"[{C_LABEL}]pares[/] [{C_CYAN}]{pair_mode}[/]",
        border_style=C_PANEL,
        box=box.ROUNDED,
    ))
    console.print()


def bot_boot(active_pairs: list, max_positions: int, poll_interval: int, dynamic_enabled: bool):
    pair_mode = "selecao dinamica" if dynamic_enabled else "lista fixa"
    console.print(Rule("[bold cyan]inicializacao[/bold cyan]", style="dim"))
    console.print(_p(
        f"[{C_LABEL}]pares ativos[/] [white]{len(active_pairs)}[/white]"
        f"   [{C_LABEL}]max posicoes[/] [white]{max_positions}[/white]"
        f"   [{C_LABEL}]intervalo[/] [white]{poll_interval}s[/white]"
        f"   [{C_LABEL}]origem[/] [white]{pair_mode}[/white]"
    ))
    preview = ", ".join(active_pairs[:8])
    suffix = " ..." if len(active_pairs) > 8 else ""
    console.print(_p(f"[{C_LABEL}]universo[/] [{C_CYAN}]{preview}{suffix}[/{C_CYAN}]"))
    console.print()


def live_confirmation_banner(
    pairs: list, balance_usdt, max_order_size_usdt: float, max_positions: int,
    daily_limit_pct: float, weekly_limit_pct: float, monthly_limit_pct: float, max_consecutive_losses: int,
):
    balance_display = f"${balance_usdt:,.2f}" if balance_usdt is not None else "indisponivel"
    console.print()
    console.print(Panel.fit(
        f"[bold {C_WARN}]MODO LIVE -- operando com dinheiro real[/bold {C_WARN}]\n\n"
        f"[{C_LABEL}]pares ativos[/] [white]{', '.join(pairs)}[/white]\n"
        f"[{C_LABEL}]saldo real[/] [{C_PRICE}]{balance_display}[/{C_PRICE}]\n"
        f"[{C_LABEL}]tamanho maximo por ordem[/] [white]${max_order_size_usdt:,.2f}[/white]\n"
        f"[{C_LABEL}]maximo de posicoes[/] [white]{max_positions}[/white]\n"
        f"[{C_LABEL}]limite de perda diario[/] [white]{daily_limit_pct * 100:.1f}%[/white]\n"
        f"[{C_LABEL}]limite de perda semanal[/] [white]{weekly_limit_pct * 100:.1f}%[/white]\n"
        f"[{C_LABEL}]limite de perda mensal[/] [white]{monthly_limit_pct * 100:.1f}%[/white]\n"
        f"[{C_LABEL}]maximo de perdas consecutivas[/] [white]{max_consecutive_losses}[/white]",
        border_style=C_WARN,
        box=box.ROUNDED,
        title="confirmacao antes de operar",
    ))
    console.print()


def fmt_or_na(value, fmt: str = ",.2f", prefix: str = "$") -> str:
    """Formata um valor monetario/numerico, ou "indisponível" quando `None`
    -- usado para caixa/patrimonio/PnL quando um preco nao pode ser
    buscado (nunca deve virar 0.0 silencioso, ver trading/portfolio.py)."""
    if value is None:
        return "indisponível"
    return f"{prefix}{value:{fmt}}"


def print_portfolio_summary(snap):
    """Caixa livre/posições/patrimônio + PnL realizado/não realizado/total --
    compartilhado entre `status` e `painel` (trading/portfolio.py
    PortfolioSnapshot) para as duas telas nunca divergirem na formatacao
    dos mesmos dados (achado de code-review: bloco estava duplicado)."""
    pnl_c = C_POS if (snap.total_pnl is None or snap.total_pnl >= 0) else C_NEG
    console.print(f"  [{C_LABEL}]caixa livre[/{C_LABEL}]   [{C_PRICE}]{fmt_or_na(snap.free_cash)}[/{C_PRICE}]"
                  f"   [{C_LABEL}]posições[/{C_LABEL}] [{C_PRICE}]{fmt_or_na(snap.positions_value)}[/{C_PRICE}]"
                  f"   [{C_LABEL}]patrimônio[/{C_LABEL}] [{C_PRICE}]{fmt_or_na(snap.total_equity)}[/{C_PRICE}]")
    console.print(f"  [{C_LABEL}]pnl realizado[/{C_LABEL}] [{C_POS if snap.realized_pnl >= 0 else C_NEG}]{fmt_or_na(snap.realized_pnl, fmt='+.2f')}[/]"
                  f"   [{C_LABEL}]pnl não realizado[/{C_LABEL}] [white]{fmt_or_na(snap.unrealized_pnl, fmt='+.2f')}[/white]"
                  f"   [{C_LABEL}]pnl total[/{C_LABEL}] [{pnl_c}]{fmt_or_na(snap.total_pnl, fmt='+.2f')}[/{pnl_c}]")


def simulation_context_banner(symbol: str, timeframe: str, period_start, period_end, initial_capital: float):
    start_str = period_start.strftime("%Y-%m-%d") if hasattr(period_start, "strftime") else str(period_start)
    end_str = period_end.strftime("%Y-%m-%d") if hasattr(period_end, "strftime") else str(period_end)
    console.print()
    console.print(Panel.fit(
        f"[bold {C_CYAN}]modo: backtest simulado[/bold {C_CYAN}]\n\n"
        f"[{C_LABEL}]par[/] [white]{symbol}[/white]"
        f"   [{C_LABEL}]timeframe[/] [white]{timeframe}[/white]\n"
        f"[{C_LABEL}]periodo testado[/] [white]{start_str} a {end_str}[/white]\n"
        f"[{C_LABEL}]capital inicial simulado[/] [white]${initial_capital:,.2f}[/white]\n\n"
        f"[{C_DIM}]resultado historico simulado -- nao reflete o saldo real do bot"
        f" (ver data/state.json)[/{C_DIM}]",
        border_style=C_CYAN,
        box=box.ROUNDED,
    ))
    console.print()


def cycle_start(cycle_id: int, active_pairs: list, open_positions: int, balance: float, daily_pnl: float):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    daily_color = _pnl_color(daily_pnl)
    console.print(Rule(f"[bold cyan]ciclo {cycle_id}[/bold cyan]  [dim]{now}[/dim]", style="dim"))
    console.print(_p(
        f"[{C_LABEL}]checando[/] [white]{len(active_pairs)} pares[/white]"
        f"   [{C_LABEL}]posicoes abertas[/] [white]{open_positions}[/white]"
        f"   [{C_LABEL}]saldo[/] [{C_PRICE}]${balance:,.2f}[/{C_PRICE}]"
        f"   [{C_LABEL}]pnl dia[/] [{daily_color}]{daily_pnl:+.2f}[/{daily_color}]"
    ))
    console.print(_p(f"[{C_DIM}]fases: candles -> indicadores -> sinais -> risco -> execucao -> resumo[/{C_DIM}]"))
    console.print()


def phase(name: str, detail: str = ""):
    suffix = f" [{C_DIM}]{detail}[/{C_DIM}]" if detail else ""
    console.print(_d(f"[bold white]{name}[/bold white]{suffix}"))


@contextmanager
def spinner(text: str):
    with console.status(f"[{C_DIM}]{text}[/{C_DIM}]", spinner="dots", spinner_style=C_CYAN):
        yield


def signal_line(price: float, signal: str, rsi: float, ema_fast: float, ema_slow: float):
    sig = _signal_markup(signal)
    rc = _rsi_color(rsi)
    console.print(_d(f"[{C_DIM}]{datetime.now().strftime('%H:%M:%S')}[/{C_DIM}]"))
    console.print(_p(f"[{C_LABEL}]preco[/] [{C_PRICE}]{_fmt_price(price)}[/]      {sig}"))
    console.print(_p(
        f"[{C_LABEL}]RSI[/] [{rc}]{rsi:.0f}[/{rc}]"
        f"   [{C_LABEL}]EMA[/] [{C_CYAN}]{_fmt_num(ema_fast)}[/] / [{C_DIM}]{_fmt_num(ema_slow)}[/]"
    ))


def position_line(entry: float, current: float, sl: float, tp: float):
    pnl = (current - entry) / entry * 100
    pc = _pnl_color(pnl)
    console.print(_p(
        f"[{C_LABEL}]posicao[/] [{C_LABEL}]entrada[/] [{C_PRICE}]{_fmt_price(entry)}[/]"
        f"   [{C_LABEL}]pnl[/] [{pc}]{pnl:+.2f}%[/{pc}]"
        f"   [{C_LABEL}]sl[/] [{C_NEG}]{_fmt_price(sl)}[/]"
        f"   [{C_LABEL}]tp[/] [{C_POS}]{_fmt_price(tp)}[/]"
    ))


def stats_line(balance: float, pnl: float, trades: int, win_rate: float):
    pc = _pnl_color(pnl)
    wc = C_POS if win_rate >= 50 else C_NEG
    console.print(_p(
        f"[{C_LABEL}]saldo[/] [{C_PRICE}]${balance:,.2f}[/]"
        f"   [{C_LABEL}]pnl[/] [{pc}]{pnl:+.2f}[/{pc}]"
        f"   [{C_LABEL}]trades[/] [white]{trades}[/white]"
        f"   [{C_LABEL}]win[/] [{wc}]{win_rate:.0f}%[/{wc}]"
    ))


def buy_opened(symbol: str, price: float, qty: float, sl: float, tp: float):
    console.print()
    console.print(Panel.fit(
        f"[{C_BUY}]compra aberta[/] [bold white]{symbol}[/]\n"
        f"[{C_LABEL}]entrada[/] [{C_PRICE}]{_fmt_price(price)}[/]   "
        f"[{C_LABEL}]qty[/] [{C_CYAN}]{qty:.6f}[/]\n"
        f"[{C_LABEL}]stop[/] [{C_NEG}]{_fmt_price(sl)}[/]   "
        f"[{C_LABEL}]alvo[/] [{C_POS}]{_fmt_price(tp)}[/]",
        border_style=C_POS,
        box=box.ROUNDED,
    ))
    console.print()


def trade_result(action: str, pnl: float, pnl_pct: float, balance):
    color = C_POS if pnl >= 0 else C_NEG
    title = "trade fechado com lucro" if pnl >= 0 else "trade fechado com perda"
    balance_str = f"${balance:,.2f}" if balance is not None else "indisponível"
    console.print()
    console.print(Panel.fit(
        f"[bold white]{action}[/]\n"
        f"[{C_LABEL}]resultado[/] [{color}]{pnl:+.4f} USDT ({pnl_pct:+.2f}%)[/{color}]   "
        f"[{C_LABEL}]saldo[/] [{C_PRICE}]{balance_str}[/]",
        title=f"[{color}]{title}[/{color}]",
        border_style=color,
        box=box.ROUNDED,
    ))
    console.print()


def pairs_table(rows: list, balance: float, pnl: float, trades: int, win_rate: float):
    console.print()
    console.print(_d(f"[{C_DIM}]{datetime.now().strftime('%H:%M:%S')}[/] [bold white]resumo dos pares[/bold white]"))

    table = Table(box=box.SIMPLE_HEAVY, show_header=True, header_style="bold cyan", border_style="dim", pad_edge=False)
    table.add_column("  par", style="white", min_width=12)
    table.add_column("preco", justify="right", min_width=11)
    table.add_column("sinal", justify="center", min_width=7)
    table.add_column("fit", justify="center", min_width=5)
    table.add_column("RSI", justify="right", min_width=5)
    table.add_column("trend", justify="right", min_width=8)
    table.add_column("vol", justify="right", min_width=7)
    table.add_column("ATR", justify="right", min_width=7)
    table.add_column("pos", justify="center", min_width=6)
    table.add_column("pnl", justify="right", min_width=8)

    for row in rows:
        signal = row.get("signal", "HOLD")
        rsi = float(row.get("rsi") or 0)
        price = float(row.get("price") or 0)
        trend_gap = float(row.get("trend_gap_pct") or 0)
        volume_ratio = float(row.get("volume_ratio") or 0)
        atr_pct = float(row.get("atr_pct") or 0)
        pnl_pct = row.get("pnl_pct")

        trend_color = _pct_color(trend_gap)
        vol_color = C_POS if volume_ratio >= 1.2 else C_WARN if volume_ratio >= 1.0 else C_DIM
        atr_color = C_WARN if atr_pct >= 5 else C_CYAN if atr_pct > 0 else C_DIM
        pos_s = f"[{C_BUY}]long[/]" if row.get("in_pos") else f"[{C_DIM}]-[/]"
        pnl_s = f"[{_pnl_color(pnl_pct)}]{pnl_pct:+.2f}%[/{_pnl_color(pnl_pct)}]" if pnl_pct is not None else f"[{C_DIM}]-[/]"

        if signal == "HOLD" and row.get("ema_aligned"):
            sig_cell = f"[{C_CYAN}]↑ hold[/{C_CYAN}]"
        else:
            sig_cell = _signal_markup(signal)

        score = row.get("buy_score", 0)
        if score == 5:
            fit_cell = f"[{C_OK}]{score}/5[/{C_OK}]"
        elif score == 4:
            fit_cell = f"[{C_CYAN}]{score}/5[/{C_CYAN}]"
        elif score == 3:
            fit_cell = f"[white]{score}/5[/white]"
        else:
            fit_cell = f"[{C_DIM}]{score}/5[/{C_DIM}]"

        table.add_row(
            f"  {row.get('symbol', '')}",
            f"[{C_PRICE}]{_fmt_price(price)}[/]" if price else f"[{C_DIM}]-[/]",
            sig_cell,
            fit_cell,
            f"[{_rsi_color(rsi)}]{rsi:.0f}[/{_rsi_color(rsi)}]" if rsi else f"[{C_DIM}]-[/]",
            f"[{trend_color}]{trend_gap:+.2f}%[/{trend_color}]",
            f"[{vol_color}]{volume_ratio:.2f}x[/{vol_color}]" if volume_ratio else f"[{C_DIM}]-[/]",
            f"[{atr_color}]{atr_pct:.2f}%[/{atr_color}]" if atr_pct else f"[{C_DIM}]-[/]",
            pos_s,
            pnl_s,
        )

    console.print(table)
    _decision_table(rows)
    stats_line(balance, pnl, trades, win_rate)
    console.print()


def cycle_summary(pair_rows: list, trade_events: list, new_entries: int, blocked_entries: int):
    signals = {"BUY": 0, "SELL": 0, "HOLD": 0, "ERR": 0}
    for row in pair_rows:
        signals[row.get("signal", "HOLD")] = signals.get(row.get("signal", "HOLD"), 0) + 1
    console.print(Panel.fit(
        f"[{C_LABEL}]sinais[/] "
        f"[{C_BUY}]BUY {signals.get('BUY', 0)}[/]  "
        f"[{C_SELL}]SELL {signals.get('SELL', 0)}[/]  "
        f"[{C_HOLD}]HOLD {signals.get('HOLD', 0)}[/]  "
        f"[{C_FAIL}]ERR {signals.get('ERR', 0)}[/]\n"
        f"[{C_LABEL}]eventos[/] [white]{len(trade_events)}[/white]   "
        f"[{C_LABEL}]novas entradas[/] [white]{new_entries}[/white]   "
        f"[{C_LABEL}]compras bloqueadas[/] [white]{blocked_entries}[/white]",
        title="[bold cyan]resumo do ciclo[/bold cyan]",
        border_style=C_PANEL,
        box=box.ROUNDED,
    ))


def _decision_table(rows: list):
    actionable = [
        row for row in rows
        if row.get("signal") in {"BUY", "SELL", "ERR"}
        or row.get("in_pos")
        or "bloqueada" in row.get("decision", "")
        or "fechou" in row.get("decision", "")
        or (row.get("ema_aligned") and row.get("signal") == "HOLD")
    ]
    if not actionable:
        console.print(_p(f"[{C_DIM}]decisoes: nenhum gatilho acionavel neste ciclo; pares seguem em monitoramento.[/{C_DIM}]"))
        return

    table = Table(box=box.SIMPLE, show_header=True, header_style="bold dim", border_style="dim", pad_edge=False)
    table.add_column("  par", style="white", min_width=12)
    table.add_column("decisao do ciclo", style="white", min_width=58)

    for row in actionable:
        table.add_row(f"  {row.get('symbol', '')}", _decision_markup(row.get("decision", "monitorando")))

    console.print(table)


def waiting(seconds: int):
    next_check = datetime.now().timestamp() + seconds
    next_time = datetime.fromtimestamp(next_check).strftime("%H:%M:%S")
    console.print()
    console.print(_p(
        f"[{C_LABEL}]proxima checagem[/] [white]{next_time}[/white]"
        f"   [{C_LABEL}]aguardando[/] [white]{seconds}s[/white]"
        f"   [{C_DIM}]proximo ciclo repetira candles -> sinais -> risco -> execucao[/]"
    ))
    console.print()


def error(msg: str):
    console.print(_err(f"[{C_DIM}]{msg}[/{C_DIM}]"))


def shutdown():
    console.print()
    console.print(Rule("[bold cyan]encerramento[/bold cyan]", style="dim"))
    console.print(_d(f"[{C_DIM}]bot encerrado.[/{C_DIM}]"))
    console.print()


def _signal_markup(signal: str):
    if signal == "BUY":
        return f"[{C_BUY}]▲ BUY[/{C_BUY}]"
    if signal == "SELL":
        return f"[{C_SELL}]▼ SELL[/{C_SELL}]"
    if signal == "ERR":
        return f"[{C_FAIL}]ERR[/{C_FAIL}]"
    return f"[{C_HOLD}]hold[/{C_HOLD}]"


def _decision_markup(decision: str):
    low = decision.lower()
    if "compr" in low or "aberta" in low:
        color = C_BUY
    elif "fech" in low or "stop" in low or "venda" in low:
        color = C_SELL
    elif "bloque" in low or "aguard" in low:
        color = C_WARN
    elif "erro" in low:
        color = C_FAIL
    else:
        color = C_DIM
    return f"[{color}]{decision}[/{color}]"
