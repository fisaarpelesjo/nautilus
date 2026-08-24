#!/usr/bin/env python3
"""
Ponto de entrada principal.

Uso:
  python main.py backtest      -- run single-pair backtest
  python main.py backtest --validate  -- backtest with train/out-of-sample split + verdict
  python main.py backtest --montecarlo  -- backtest with Monte Carlo drawdown/ruin estimate
  python main.py edge          -- run profitability edge report
  python main.py multibacktest -- run backtest on fixed pair list
  python main.py scan          -- backtest top 30 pairs by volume
  python main.py compare       -- compare multiple strategies/presets side by side
  python main.py optimize      -- grid search best parameters
  python main.py optimize --validate      -- grid search with train/validation split
  python main.py optimize --walk-forward  -- validate winner across sliding windows
  python main.py analyze       -- analyze backtest results
  python main.py decisions     -- summarize data/decisions.csv (signals, blockers)
  python main.py select        -- select dynamic pairs
  python main.py chart [PAIR] [TF] [N]  -- terminal chart with EMAs and RSI
  python main.py bot           -- start the trading bot
  python main.py status        -- show balance and open positions
  python main.py kill          -- suspend new entries (kill switch)
  python main.py resume        -- resume new entries (kill switch)
"""
import sys
from config.settings import SYMBOL, TIMEFRAME, TRADING_MODE

PERFORMANCE_REPORT_PATH = "data/performance_report.html"

def cmd_backtest():
    from utils.report_export import export_report

    args = sys.argv[2:]
    if "--validate" in args:
        import dataclasses
        from backtesting.validation import run_backtest_with_validation
        train_result, validation_result, verdict = run_backtest_with_validation(SYMBOL, TIMEFRAME)
        export_report(
            "backtest_validate", {"symbol": SYMBOL, "timeframe": TIMEFRAME},
            {
                "train": dataclasses.asdict(train_result),
                "validation": dataclasses.asdict(validation_result) if validation_result else None,
                "verdict": dataclasses.asdict(verdict),
            },
        )
        return
    from backtesting.engine import run_backtest
    result = run_backtest(SYMBOL, TIMEFRAME)
    if "--montecarlo" in args:
        from backtesting.robustness import run_monte_carlo_report
        run_monte_carlo_report(result.trades)
    export_report("backtest", {"symbol": SYMBOL, "timeframe": TIMEFRAME}, result)

def cmd_edge():
    from backtesting.validation import run_edge_report
    validate = "--validate" in sys.argv[2:]
    run_edge_report(SYMBOL, TIMEFRAME, validate=validate)

def cmd_multibacktest():
    from backtesting.multi import run
    from utils.report_export import export_report

    results = run()
    export_report("multibacktest", {}, {"total_pairs": len(results)}, ranking=results)

def cmd_scan():
    from backtesting.scanner import run
    from utils.report_export import export_report

    results = run()
    export_report("scan", {}, {"total_pairs": len(results)}, ranking=results)

def cmd_comparar():
    from backtesting.compare import run
    run()

def cmd_multimarket():
    """Varredura estrategia x simbolo com confirmacao fora da amostra (spec 023).

    Existe separado de `compare` porque a pergunta e outra: `compare` mostra
    como cada combinacao se saiu; `multimarket` responde se alguma se sustenta
    FORA da janela onde foi descoberta. Testar muitas combinacoes produz
    aprovacoes por acaso, e sem essa distincao a tabela venderia sorte como
    descoberta.
    """
    from rich import box
    from rich.table import Table

    from backtesting.multimarket import run_scan
    from config.settings import RESEARCH_SYMBOLS, TIMEFRAME
    from strategy.breakout import BreakoutStrategy
    from strategy.ema_rsi import EmaRsiStrategy
    from utils.display import C_CYAN, C_DIM, C_LABEL, C_NEG, C_POS, console, header
    from utils.report_export import export_report

    simbolos = sys.argv[2:] or RESEARCH_SYMBOLS
    if not simbolos:
        print("Nenhum simbolo. Use: python main.py multimarket AAPL EURUSD=X ...")
        print("Ou defina RESEARCH_SYMBOLS no .env (aceita cripto, acoes, forex, futuros, indices).")
        return

    estrategias = {"EMA/RSI": EmaRsiStrategy(), "Breakout 150": BreakoutStrategy(window=150)}

    header()
    console.print(f"[bold {C_CYAN}]varredura multi-mercado[/]")
    console.print(f"  [{C_DIM}]{len(estrategias)} estrategias x {len(simbolos)} simbolos, "
                  f"timeframe {TIMEFRAME} -- cada combinacao e confirmada numa janela "
                  f"que nao participou da busca[/{C_DIM}]")
    console.print()

    resultado = run_scan(estrategias, simbolos, timeframe=TIMEFRAME)

    # Contagem em destaque ANTES da tabela: uma aprovacao entre 200 tentativas
    # tem peso estatistico diferente de uma entre 3, e ler a tabela sem esse
    # numero convida exatamente a leitura errada (FR-013).
    console.print(f"  [{C_LABEL}]combinacoes avaliadas[/{C_LABEL}] [white]{resultado.combinations_tested}[/white]")
    confirmados = sum(1 for e in resultado.entries if e.status == "confirmado")
    console.print(f"  [{C_LABEL}]confirmadas fora da amostra[/{C_LABEL}] [white]{confirmados}[/white]")
    console.print()

    cores = {"confirmado": C_POS, "so_na_busca": C_CYAN, "reprovado": C_NEG,
             "inconclusivo": C_DIM, "erro": C_NEG}
    rotulos = {"confirmado": "confirmado", "so_na_busca": "so na busca",
               "reprovado": "reprovado", "inconclusivo": "inconclusivo", "erro": "erro"}

    tabela = Table(box=box.ROUNDED, header_style="bold cyan")
    for coluna in ["Estrategia", "Simbolo", "Mercado"]:
        tabela.add_column(coluna)
    for coluna in ["Trades busca", "Ret busca", "Trades confirm", "Ret confirm", "PF confirm"]:
        tabela.add_column(coluna, justify="right")
    tabela.add_column("Status")

    for e in resultado.ranked():
        if e.status == "erro":
            tabela.add_row(e.strategy_name, e.symbol, "-", "-", "-", "-", "-", "-",
                           f"[{C_NEG}]erro: {(e.error or '')[:30]}[/{C_NEG}]")
            continue
        c = e.confirmation_result
        gap = " *" if e.has_session_gaps else ""
        tabela.add_row(
            e.strategy_name, e.symbol + gap, e.market or "-",
            str(e.search_result.total_trades), f"{e.search_result.total_return_pct:+.2f}%",
            str(c.total_trades) if c else "-", f"{c.total_return_pct:+.2f}%" if c else "-",
            f"{c.profit_factor:.2f}" if c else "-",
            f"[{cores[e.status]}]{rotulos[e.status]}[/{cores[e.status]}]",
        )

    console.print(tabela)
    console.print(f"  [{C_DIM}]* mercado com pregao descontinuo: o teto de perda por trade "
                  f"nao age dentro de um gap de abertura[/{C_DIM}]")
    console.print(f"  [{C_DIM}]\"so na busca\" NAO e aprovacao -- passou onde foi descoberto "
                  f"e nao se sustentou fora[/{C_DIM}]")

    export_report(
        "multimarket",
        {"strategies": list(estrategias), "symbols": simbolos, "timeframe": TIMEFRAME,
         "combinations_tested": resultado.combinations_tested},
        {"combinations_tested": resultado.combinations_tested, "confirmed": confirmados},
        ranking=resultado.ranked(),
    )
    return resultado

def cmd_analisar():
    from backtesting.analysis import run
    run()

def cmd_decisions():
    from data.decisions_analysis import run
    run()

def cmd_otimizar():
    from backtesting.optimizer import run
    from utils.report_export import export_report

    args = sys.argv[2:]
    walk_forward = "--walk-forward" in args
    validate = walk_forward or "--validate" in args
    results = run(validate=validate, walk_forward=walk_forward)
    if results is not None:
        export_report(
            "optimize", {"validate": validate, "walk_forward": walk_forward},
            {"total_results": len(results)}, ranking=results,
        )

def cmd_selecionar():
    from market.commands import run
    run()

def cmd_chart():
    from utils.chart import run
    args = sys.argv[2:]
    symbol   = args[0].upper() if len(args) > 0 else None
    timeframe = args[1]        if len(args) > 1 else None
    limit    = int(args[2])    if len(args) > 2 else 100
    run(symbol=symbol, timeframe=timeframe, limit=limit)


def cmd_bot():
    from trading.runner import run
    run()

def _toggle_killswitch(active: bool):
    from datetime import datetime
    from data.killswitch_store import save_killswitch
    from utils.logger import log_event, safe_step, get_logger
    from utils.notifier import send_telegram

    log = get_logger("cli")
    save_killswitch(active)
    label = "ativado" if active else "desativado"
    safe_step(log, f"Kill switch {label}, mas falha ao publicar evento",
              lambda: log_event("killswitch_toggled", active=active))
    safe_step(log, f"Kill switch {label}, mas falha ao enviar alerta",
              lambda: send_telegram(f"Kill switch {label.upper()} via CLI — novas entradas {'suspensas' if active else 'liberadas'}."))
    print(f"Kill switch {label} em {datetime.now().isoformat()}")

def cmd_kill():
    _toggle_killswitch(True)

def cmd_resume():
    _toggle_killswitch(False)

def cmd_status():
    from data.killswitch_store import load_killswitch
    from execution.order_manager import OrderManager
    from trading.portfolio import compute_portfolio_snapshot
    from utils.display import console, header, C_LABEL, C_PRICE, C_POS, C_NEG, C_DIM, C_CYAN, _fmt_price, print_portfolio_summary

    header()
    manager = OrderManager()
    snap = compute_portfolio_snapshot(manager)

    total       = manager.total_trades
    wins        = manager.winning_trades
    positions   = manager.positions
    win_rate    = (wins / total * 100) if total else 0
    consecutive_losses     = manager.consecutive_losses
    circuit_breaker_active = manager.circuit_breaker_active
    killswitch_active = load_killswitch()
    wc      = C_POS if win_rate >= 50 else C_NEG

    print_portfolio_summary(snap)
    console.print(f"  [{C_LABEL}]trades[/{C_LABEL}] [white]{total}[/white]"
                  f"   [{C_LABEL}]win rate[/{C_LABEL}] [{wc}]{win_rate:.0f}%[/{wc}]")
    console.print()

    if killswitch_active or circuit_breaker_active:
        if killswitch_active:
            console.print(f"  [{C_NEG}]kill switch ATIVADO[/{C_NEG}] — novas entradas suspensas manualmente")
        if circuit_breaker_active:
            console.print(
                f"  [{C_NEG}]circuit breaker ATIVADO[/{C_NEG}] — {consecutive_losses} perdas seguidas, novas entradas suspensas"
            )
        console.print()

    if positions:
        console.print(f"  [{C_LABEL}]posições abertas ({len(positions)}):[/{C_LABEL}]")
        for symbol, pos in positions.items():
            # Reusa o preco ja buscado por compute_portfolio_snapshot() --
            # buscar de novo aqui duplicaria a chamada de rede e podia
            # divergir do total agregado acima (achado de code-review).
            current = snap.prices.get(symbol)
            if current is None:
                console.print(f"  [{C_DIM}]{symbol}  erro ao buscar preço[/{C_DIM}]")
                continue
            pnl_pct = (current - pos.entry_price) / pos.entry_price * 100
            pc2     = C_POS if pnl_pct >= 0 else C_NEG
            console.print(
                f"  [{C_CYAN}]{symbol}[/{C_CYAN}]"
                f"  [{C_LABEL}]entrada[/{C_LABEL}] [{C_PRICE}]{_fmt_price(pos.entry_price)}[/{C_PRICE}]"
                f"  [{C_LABEL}]atual[/{C_LABEL}] [{C_PRICE}]{_fmt_price(current)}[/{C_PRICE}]"
                f"  [{pc2}]{pnl_pct:+.2f}%[/{pc2}]"
            )
    else:
        console.print(f"  [{C_DIM}]nenhuma posição aberta[/{C_DIM}]")
    console.print()

    if TRADING_MODE == "live":
        last_reconciliation = manager.last_reconciliation
        if last_reconciliation:
            status = last_reconciliation.get("status", "?")
            checked_at = last_reconciliation.get("checked_at", "?")
            rc = C_POS if status == "ok" else C_NEG
            console.print(
                f"  [{C_LABEL}]reconciliação[/{C_LABEL}] [{rc}]{status}[/{rc}]"
                f"   [{C_LABEL}]em[/{C_LABEL}] [{C_DIM}]{checked_at}[/{C_DIM}]"
            )
            for diff in last_reconciliation.get("diffs", []):
                console.print(f"  [{C_NEG}]  {diff}[/{C_NEG}]")
        else:
            console.print(f"  [{C_DIM}]reconciliação ainda não rodou nesta sessão[/{C_DIM}]")
        console.print()

def cmd_painel():
    from execution.order_manager import OrderManager
    from trading.panel import print_panel

    manager = OrderManager()
    print_panel(manager)

def cmd_performance():
    import webbrowser
    from pathlib import Path
    from backtesting.performance_charts import build_performance_figures
    from data.trade_store import load_recent_trades

    trades = load_recent_trades(n=100_000)
    figures = build_performance_figures(trades)

    if figures.status == "sem_dados":
        print("Nenhum trade encontrado em data/trades.csv ainda -- nada para exibir.")
        return

    parts = [
        figures.capital_curve.to_html(full_html=False, include_plotlyjs="cdn"),
        figures.drawdown_curve.to_html(full_html=False, include_plotlyjs=False),
        figures.pnl_by_pair.to_html(full_html=False, include_plotlyjs=False),
    ]
    html = "<html><body>" + "".join(parts) + "</body></html>"

    report_path = Path(PERFORMANCE_REPORT_PATH)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(html, encoding="utf-8")

    # PERFORMANCE_REPORT_PATH e relativo por padrao -- um f"file://{path}"
    # direto produz uma URL malformada (o navegador interpreta o primeiro
    # segmento como host, nao como parte do caminho). resolve().as_uri()
    # gera sempre um file:/// absoluto valido.
    webbrowser.open(report_path.resolve().as_uri())

def cmd_replay():
    from backtesting.engine import simulate_backtest
    from data.fetcher import fetch_ohlcv
    from strategy.ema_rsi import EmaRsiStrategy
    from trading.replay import compare_to_backtest, run_replay
    from utils.display import C_CYAN, C_DIM, C_LABEL, console, header, _pct_color

    args = sys.argv[2:]
    symbol = args[0] if args else SYMBOL

    header()
    console.print(f"[bold {C_CYAN}]replay: {symbol}[/bold {C_CYAN}]")
    console.print(f"  [{C_DIM}]rodando o caminho de decisao real sobre historico publico -- isolado, nenhum arquivo real do bot e tocado[/{C_DIM}]")
    console.print()

    # candle_limit menor que o default de run_backtest/run_replay: cada
    # ciclo do replay recalcula indicadores sobre uma janela crescente (o
    # mesmo padrao ja aceito em backtesting/engine.py simulate_backtest sem
    # precomputed_signals) -- com 2000 candles isso passa de 1 minuto real.
    # 300 mantem o comando usavel sob demanda, custando ~1 mes de historico
    # em 4h.
    replay_candle_limit = 300
    initial_capital = 1000.0
    result = run_replay(symbol, TIMEFRAME, candle_limit=replay_candle_limit)

    # simulate_backtest() em vez de run_backtest(): run_backtest() imprime
    # seu proprio relatorio completo internamente (print_report), o que
    # poluiria a saida deste comando com um bloco de backtest inteiro antes
    # da comparacao concisa pretendida (achado de code-review).
    # initial_capital MUST ser o mesmo valor passado a compare_to_backtest()
    # abaixo -- sem isso, os dois retornos % comparados nao teriam a mesma
    # base de capital (outro achado de code-review: coincidencia de
    # defaults duplicados, nao um vinculo real).
    df = fetch_ohlcv(symbol, TIMEFRAME, limit=replay_candle_limit)
    strategy = EmaRsiStrategy()
    prepared = strategy.calculate_indicators(df)
    backtest_result = simulate_backtest(prepared, strategy, initial_capital=initial_capital)
    comparison = compare_to_backtest(result, backtest_result, initial_capital=initial_capital)

    # _pct_color (mesma usada em outros relatorios do bot) trata exatamente
    # 0% como neutro (C_DIM), nao positivo -- um ternario inline aqui
    # divergiria dessa convencao ja estabelecida (achado de code-review).
    console.print(f"  [{C_LABEL}]replay[/{C_LABEL}]    trades [white]{comparison.replay_trades}[/white]"
                  f"   retorno [{_pct_color(comparison.replay_return_pct)}]{comparison.replay_return_pct:+.2f}%[/]"
                  f"   bloqueios [white]{result.blocked_cycles}[/white]")
    console.print(f"  [{C_LABEL}]backtest[/{C_LABEL}]  trades [white]{comparison.backtest_trades}[/white]"
                  f"   retorno [{_pct_color(comparison.backtest_return_pct)}]{comparison.backtest_return_pct:+.2f}%[/]")
    console.print()
    for note in comparison.notes:
        console.print(f"  [{C_DIM}]- {note}[/{C_DIM}]")

def cmd_debug():
    from data.fetcher import fetch_ohlcv
    from execution.order_manager import OrderManager
    from strategy.diagnostics import full_diagnosis
    from strategy.ema_rsi import EmaRsiStrategy
    from trading.position_lifecycle import mtf_confirmed
    from utils.display import C_DIM, C_LABEL, C_NEG, C_POS, console, header

    args = sys.argv[2:]
    symbol = args[0] if args else SYMBOL

    header()
    strategy = EmaRsiStrategy()
    df = fetch_ohlcv(symbol, TIMEFRAME)
    prepared = strategy.calculate_indicators(df)
    if len(prepared) < 2:
        console.print(f"  [{C_NEG}]{symbol}: dados insuficientes para diagnostico[/{C_NEG}]")
        return

    indicators = prepared.iloc[-1]
    previous = prepared.iloc[-2]
    current_price = float(indicators["close"])

    manager = OrderManager()
    cooldown_active = manager.is_in_cooldown(symbol)
    mtf_ok = mtf_confirmed(symbol, current_price, strategy)

    diagnosis = full_diagnosis(indicators, previous, current_price, strategy, mtf_ok=mtf_ok, cooldown_active=cooldown_active)

    console.print(f"[bold]diagnostico: {symbol}[/bold]  preco ${current_price:.4f}")
    console.print()
    for key, value in diagnosis.items():
        ok = value is True
        color = C_POS if ok else (C_NEG if value is False else C_DIM)
        console.print(f"  [{C_LABEL}]{key}[/{C_LABEL}]  [{color}]{value}[/{color}]")

COMMANDS = {
    "backtest":      cmd_backtest,
    "edge":          cmd_edge,
    "multibacktest": cmd_multibacktest,
    "scan":          cmd_scan,
    "compare":       cmd_comparar,
    "multimarket":   cmd_multimarket,
    "multimercado":  cmd_multimarket,
    "analyze":       cmd_analisar,
    "decisions":     cmd_decisions,
    "optimize":      cmd_otimizar,
    "select":        cmd_selecionar,
    "chart":         cmd_chart,
    "bot":           cmd_bot,
    "status":        cmd_status,
    "kill":          cmd_kill,
    "resume":        cmd_resume,
    "painel":        cmd_painel,
    "debug":         cmd_debug,
    "performance":   cmd_performance,
    "desempenho":    cmd_performance,
    "replay":        cmd_replay,
    # aliases pt-br
    "analisar":      cmd_analisar,
    "decisoes":      cmd_decisions,
    "otimizar":      cmd_otimizar,
    "selecionar":    cmd_selecionar,
    "comparar":      cmd_comparar,
}

if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "bot"
    if cmd not in COMMANDS:
        print(f"Comando invalido. Use: {', '.join(COMMANDS)}")
        sys.exit(1)
    COMMANDS[cmd]()
