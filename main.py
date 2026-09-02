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
    from strategy.day_filter import DayFilterStrategy
    from strategy.ema_rsi import EmaRsiStrategy
    from strategy.mean_reversion import MeanReversionStrategy
    from strategy.squeeze_breakout import SqueezeBreakoutStrategy
    from utils.display import C_CYAN, C_DIM, C_LABEL, C_NEG, C_POS, console, header
    from utils.report_export import export_report

    simbolos = sys.argv[2:] or RESEARCH_SYMBOLS
    if not simbolos:
        print("Nenhum simbolo. Use: python main.py multimarket AAPL EURUSD=X ...")
        print("Ou defina RESEARCH_SYMBOLS no .env (aceita cripto, acoes, forex, futuros, indices).")
        return

    # As cinco da mesma lista de `compare`, para os dois comandos responderem
    # sobre o mesmo conjunto. Aqui cada uma passa pela confirmacao fora da
    # amostra, que e o que separa aprovacao real de aprovacao por acaso --
    # quanto mais combinacoes na varredura, mais isso importa.
    from backtesting.compare import DIA_BLOQUEADO_SEGUNDA

    estrategias = {
        "EMA/RSI": EmaRsiStrategy(),
        "Breakout 150": BreakoutStrategy(window=150),
        "Mean Reversion": MeanReversionStrategy(),
        "Squeeze Breakout": SqueezeBreakoutStrategy(),
        "EMA/RSI sem segunda": DayFilterStrategy(EmaRsiStrategy(), DIA_BLOQUEADO_SEGUNDA),
    }

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

    cores = {"confirmado": C_POS, "defensivo": C_CYAN, "so_na_busca": C_CYAN, "reprovado": C_NEG,
             "inconclusivo": C_DIM, "erro": C_NEG}
    rotulos = {"confirmado": "confirmado", "defensivo": "defensivo", "so_na_busca": "so na busca",
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


def cmd_horizonte():
    """H11 -- avalia as estrategias em horizonte diario e semanal.

    Nao altera o TIMEFRAME de producao (FR-012): le a configuracao apenas para
    exibir a linha de base. Universo e estrategias NAO sao parametrizaveis por
    CLI de proposito -- expor os dois como flag convidaria a varrer combinacoes
    ate achar uma que passe, que e o mecanismo de testes multiplos que a
    confirmacao fora da amostra existe para conter.
    """
    from rich import box
    from rich.table import Table

    from backtesting.horizonte import (
        ESTRATEGIAS_H11,
        UNIVERSO_H11,
        folds_uteis,
        run_horizonte_scan,
    )
    from config.settings import TIMEFRAME
    from utils.display import C_CYAN, C_DIM, C_LABEL, C_NEG, C_POS, console, header
    from utils.report_export import export_report

    horizontes = sys.argv[2:] or ["4h", "1d", "1w"]
    pares = list(UNIVERSO_H11)
    estrategias = ESTRATEGIAS_H11()

    header()
    console.print(f"[bold {C_CYAN}]varredura por horizonte temporal (H11)[/]")
    console.print(f"  [{C_DIM}]{len(estrategias)} estrategias x {len(horizontes)} horizontes "
                  f"x {len(pares)} pares -- horizonte de producao {TIMEFRAME}, inalterado[/{C_DIM}]")
    console.print()

    relatorios = run_horizonte_scan(estrategias, pares, horizontes)

    cores = {"confirmado": C_POS, "so_na_busca": C_CYAN, "reprovado": C_NEG,
             "inconclusivo": C_DIM, "erro": C_NEG}
    rotulos = {"confirmado": "confirmado", "so_na_busca": "so na busca",
               "reprovado": "reprovado", "inconclusivo": "inconclusivo", "erro": "erro"}

    for rel in relatorios:
        console.print(f"[bold]{rel.horizonte}[/bold]")

        # Contexto de dado ANTES de tudo (T032, FR-009/FR-010): sem ele, uma
        # tabela de resultados semanais parece comparavel a uma diaria.
        curtos = sorted({c.par for c in rel.combinacoes if c.disponibilidade.historico_curto})
        console.print(f"  [{C_LABEL}]candles medianos[/{C_LABEL}] [white]{rel.candles_medianos}[/white]"
                      f"   [{C_LABEL}]aquecimento[/{C_LABEL}] "
                      f"[white]{rel.aquecimento_dias_horizonte:.0f} dias[/white]")
        if curtos:
            console.print(f"  [{C_LABEL}]historico curto[/{C_LABEL}] "
                          f"[{C_DIM}]{', '.join(x.replace('/USDT', '') for x in curtos)}[/{C_DIM}]")

        # Contagem ANTES da tabela: uma confirmacao entre 144 tentativas tem
        # peso estatistico distinto de uma entre 3.
        console.print(f"  [{C_LABEL}]avaliadas[/{C_LABEL}] [white]{rel.n_avaliadas}[/white]"
                      f"   [{C_LABEL}]confirmadas fora da amostra[/{C_LABEL}] "
                      f"[white]{rel.n_confirmadas}[/white]"
                      f"   [{C_LABEL}]inconclusivas[/{C_LABEL}] "
                      f"[white]{rel.n_inconclusivas}[/white]")
        console.print()

        tabela = Table(box=box.SIMPLE_HEAVY, title=None, header_style=C_LABEL)
        for col in ("Estrategia", "Par", "Trades", "Ret %", "B&H %",
                    "Sem custo %", "Custo pp", "PF", "DD %", "Timing pp", "Status"):
            tabela.add_column(col, justify="left" if col in ("Estrategia", "Par", "Status") else "right")

        for c in rel.ordenadas():
            r = c.resultado_janela_unica
            trades = f"{r.total_trades}" if r else "-"
            ret = f"{r.total_return_pct:.2f}" if r else "-"
            bh = f"{r.buy_hold_return_pct:.2f}" if r else "-"
            pf = f"{r.profit_factor:.2f}" if r else "-"
            dd = f"{r.max_drawdown_pct:.2f}" if r else "-"
            sem = f"{c.retorno_sem_custo_pct:.2f}" if c.retorno_sem_custo_pct is not None else "-"
            custo = (f"{r.total_return_pct - c.retorno_sem_custo_pct:+.2f}"
                     if r and c.retorno_sem_custo_pct is not None else "-")
            uteis = folds_uteis(c.folds)
            timing = (f"{sum(f.ganho_de_timing_pp for f in uteis) / len(uteis):+.2f}"
                      if uteis else "-")
            cor = cores.get(c.status, C_DIM)
            tabela.add_row(c.estrategia, c.par.replace("/USDT", ""), trades, ret, bh,
                           sem, custo, pf, dd, timing,
                           f"[{cor}]{rotulos.get(c.status, c.status)}[/{cor}]")

        console.print(tabela)
        console.print()

    # Quadro comparativo entre horizontes (T024): horizonte maior negocia menos
    # e paga menos taxa, e essa e exatamente a confusao que US2 existe para
    # desfazer -- por isso o impacto de custo aparece lado a lado.
    console.print(f"[bold {C_CYAN}]comparativo entre horizontes[/]")
    comp = Table(box=box.SIMPLE_HEAVY, header_style=C_LABEL)
    for col in ("Horizonte", "Avaliadas", "Confirmadas", "Inconclusivas",
                "Candles med.", "Aquec. dias", "Custo medio pp"):
        comp.add_column(col, justify="left" if col == "Horizonte" else "right")
    for rel in relatorios:
        impactos = [c.resultado_janela_unica.total_return_pct - c.retorno_sem_custo_pct
                    for c in rel.combinacoes
                    if c.resultado_janela_unica and c.retorno_sem_custo_pct is not None]
        medio = f"{sum(impactos) / len(impactos):+.2f}" if impactos else "-"
        comp.add_row(rel.horizonte, str(rel.n_avaliadas), str(rel.n_confirmadas),
                     str(rel.n_inconclusivas), str(rel.candles_medianos),
                     f"{rel.aquecimento_dias_horizonte:.0f}", medio)
    console.print(comp)
    console.print()

    # Legenda (T019): sem ela, "so na busca" e lido como aprovacao fraca e
    # "inconclusivo" como reprovacao.
    console.print(f"  [{C_DIM}]\"so na busca\" NAO e aprovacao -- passou onde foi descoberta "
                  f"e nao se sustentou fora[/{C_DIM}]")
    console.print(f"  [{C_DIM}]\"inconclusivo\" significa amostra insuficiente para julgar, "
                  f"nao ausencia de vantagem[/{C_DIM}]")
    console.print(f"  [{C_DIM}]\"Custo pp\" e quanto a taxa e o slippage retiraram do retorno "
                  f"bruto[/{C_DIM}]")

    export_report(
        "horizonte",
        {"horizontes": horizontes, "pares": pares, "estrategias": list(estrategias)},
        [{"horizonte": rel.horizonte, "avaliadas": rel.n_avaliadas,
          "confirmadas": rel.n_confirmadas, "inconclusivas": rel.n_inconclusivas,
          "candles_medianos": rel.candles_medianos,
          "combinacoes": [{"estrategia": c.estrategia, "par": c.par,
                           "status": c.status, "motivo": c.motivo,
                           "trades": c.resultado_janela_unica.total_trades if c.resultado_janela_unica else 0,
                           "retorno_pct": c.resultado_janela_unica.total_return_pct if c.resultado_janela_unica else None,
                           "retorno_sem_custo_pct": c.retorno_sem_custo_pct,
                           "n_janelas": c.n_janelas}
                          for c in rel.ordenadas()]}
         for rel in relatorios],
    )


def cmd_volatilidade():
    """H12 -- dimensionamento de posicao por volatilidade.

    Compara cada estrategia consigo mesma, com e sem dimensionamento, sobre a
    mesma serie. Universo e estrategias nao sao parametrizaveis por CLI, pelo
    mesmo motivo de `horizonte`. O alvo aceita argumento para inspecao manual e
    reprodutibilidade, nao para varredura: varrer alvos ate um passar e o
    problema de testes multiplos que a metodologia existe para conter.
    """
    from rich import box
    from rich.table import Table

    from backtesting.volatilidade import (
        ALVO_PADRAO,
        ParametrosVolatilidade,
        run_volatilidade_scan,
    )
    from utils.display import C_CYAN, C_DIM, C_LABEL, C_NEG, C_POS, console, header
    from utils.report_export import export_report

    alvo = ALVO_PADRAO
    if len(sys.argv) > 2:
        try:
            alvo = float(sys.argv[2])
        except ValueError:
            print(f"alvo invalido: {sys.argv[2]}")
            sys.exit(1)
        if not alvo > 0:
            print(f"alvo precisa ser positivo: {alvo}")
            sys.exit(1)

    params = ParametrosVolatilidade(alvo=alvo)

    header()
    console.print(f"[bold {C_CYAN}]dimensionamento por volatilidade (H12)[/]")
    console.print(f"  [{C_DIM}]alvo {alvo:.4f} -- fator = min(1,0; alvo / atr_ratio), "
                  f"so reduz posicao, nunca amplia[/{C_DIM}]")
    console.print(f"  [{C_DIM}]risk/manager.py nao e tocado: producao continua "
                  f"dimensionando como hoje[/{C_DIM}]")
    console.print()

    comparacoes = run_volatilidade_scan(params=params)

    ordem = {"melhora": 0, "so_na_busca": 1, "confundido": 2, "sem_vantagem": 3,
             "piora": 4, "inconclusivo": 5, "inerte": 6, "erro": 7}
    comparacoes.sort(key=lambda c: (ordem.get(c.status, 9), -c.delta_timing))

    conta = {k: sum(1 for c in comparacoes if c.status == k) for k in ordem}
    inertes = conta["inerte"]
    avaliadas = [c for c in comparacoes
                 if c.status in ("melhora", "so_na_busca", "confundido",
                                 "sem_vantagem", "piora")]
    fatores = [c.fator_medio for c in comparacoes if c.sem_dimensionamento is not None]

    # Contagem ANTES da tabela: quem le uma tabela de 48 linhas forma a
    # impressao pelas primeiras que ve, e o numero agregado e o resultado.
    console.print(f"  [{C_LABEL}]avaliadas[/] {len(avaliadas)}  "
                  f"[{C_POS}]melhora[/] {conta['melhora']}  "
                  f"[{C_CYAN}]so na busca[/] {conta['so_na_busca']}  "
                  f"[{C_CYAN}]confundidas[/] {conta['confundido']}  "
                  f"[{C_DIM}]sem vantagem[/] {conta['sem_vantagem']}  "
                  f"[{C_NEG}]piora[/] {conta['piora']}  "
                  f"[{C_DIM}]inconclusivas[/] {conta['inconclusivo']}  "
                  f"[{C_DIM}]inertes[/] {inertes}  "
                  f"[{C_DIM}]erro[/] {conta['erro']}")
    if fatores:
        console.print(f"  [{C_LABEL}]fator medio aplicado[/] "
                      f"{sum(fatores) / len(fatores):.3f}")
    console.print()

    t = Table(box=box.SIMPLE_HEAD)
    for col in ("Estrategia", "Par"):
        t.add_column(col)
    for col in ("DD base", "DD dim", "dDD", "Ret base", "Ret dim", "dRet",
                "dExpo", "dExpoTempo", "dTiming", "Ops", "dCusto"):
        t.add_column(col, justify="right")
    t.add_column("Status")

    cores = {"melhora": C_POS, "piora": C_NEG, "inerte": C_DIM,
             "so_na_busca": C_CYAN, "confundido": C_CYAN}
    for c in comparacoes:
        b, d = c.sem_dimensionamento, c.com_dimensionamento
        cor = cores.get(c.status, C_DIM)
        rotulo = c.status.replace("_", " ")
        if b is None or d is None:
            t.add_row(c.estrategia, c.par, *["-"] * 11,
                      f"[{cor}]{rotulo}[/{cor}]")
            continue
        medido = c.retorno_sem_custo_base is not None and c.retorno_sem_custo_dim is not None
        t.add_row(
            c.estrategia, c.par,
            f"{b.max_drawdown_pct:.2f}", f"{d.max_drawdown_pct:.2f}",
            f"{c.delta_drawdown:+.2f}",
            f"{b.total_return_pct:.2f}", f"{d.total_return_pct:.2f}",
            f"{c.delta_retorno:+.2f}",
            f"{c.delta_exposicao:+.2f}", f"{c.delta_exposicao_tempo:+.1f}",
            f"{c.delta_timing:+.3f}",
            f"{b.total_trades}/{d.total_trades}",
            # "-" e nao "0,00": custo nao medido nao e custo nulo.
            f"{c.delta_custo:+.2f}" if medido else "-",
            f"[{cor}]{rotulo}[/{cor}]",
        )
    console.print(t)
    console.print()

    # Legenda: sem ela, "sem vantagem" e lido como melhora fraca -- que e
    # exatamente a leitura errada que US2 existe para impedir.
    console.print(f"  [{C_DIM}]\"sem vantagem\": o drawdown caiu mas o ganho desapareceu "
                  f"ao descontar exposicao -- participar menos nao e habilidade[/{C_DIM}]")
    console.print(f"  [{C_DIM}]\"inconclusivo\" significa amostra insuficiente para julgar, "
                  f"nao ausencia de vantagem[/{C_DIM}]")
    console.print(f"  [{C_DIM}]\"inerte\": o fator ficou em 1,0 e as duas versoes sao a mesma "
                  f"execucao -- nada foi medido, nao houve piora[/{C_DIM}]")
    console.print(f"  [{C_DIM}]dTiming e o ganho POR UNIDADE DE CAPITAL EXPOSTO: invariante sob "
                  f"redimensionamento puro, move-se so com reducao seletiva[/{C_DIM}]")
    console.print(f"  [{C_DIM}]\"confundido\": a base PERDE dinheiro, entao encolher a posicao "
                  f"aproxima de zero -- o limite dessa logica e nao operar[/{C_DIM}]")
    console.print(f"  [{C_DIM}]\"so na busca\" NAO e aprovacao: melhorou onde foi medido e nao "
                  f"se sustentou na validacao fora da amostra[/{C_DIM}]")
    console.print(f"  [{C_DIM}]dExpo e exposicao de CAPITAL; a de tempo nao se move sob este "
                  f"mecanismo (dExpoTempo, exibida para provar isso)[/{C_DIM}]")

    # Agregado de custo de giro (T030). Responde se a diferenca entre versoes
    # persiste com custo zerado -- se o dRet medio for negativo mas o dRet medio
    # sem custo for positivo, o mecanismo ajuda e o giro come o ganho, que e
    # conclusao diferente de "o mecanismo nao ajuda".
    com_custo = [c for c in avaliadas
                 if c.retorno_sem_custo_base is not None
                 and c.retorno_sem_custo_dim is not None]
    if com_custo:
        n = len(com_custo)
        d_ret = sum(c.delta_retorno for c in com_custo) / n
        d_sem = sum(c.retorno_sem_custo_dim - c.retorno_sem_custo_base
                    for c in com_custo) / n
        d_custo = sum(c.delta_custo for c in com_custo) / n
        d_ops = sum(c.delta_operacoes for c in com_custo) / n
        console.print()
        console.print(f"  [{C_LABEL}]custo de giro[/] em {n} comparacoes: "
                      f"dRet medio {d_ret:+.2f}pp, "
                      f"dRet sem custo {d_sem:+.2f}pp, "
                      f"diferenca atribuivel a custo {d_custo:+.2f}pp, "
                      f"dOperacoes medio {d_ops:+.1f}")

    export_report(
        "volatilidade",
        {"alvo": alvo, "fator_minimo": params.fator_minimo,
         "pares": len(set(c.par for c in comparacoes)),
         "estrategias": sorted(set(c.estrategia for c in comparacoes))},
        [{"estrategia": c.estrategia, "par": c.par, "status": c.status,
          "motivo": c.motivo, "fator_medio": c.fator_medio,
          "drawdown_base": c.sem_dimensionamento.max_drawdown_pct if c.sem_dimensionamento else None,
          "drawdown_dim": c.com_dimensionamento.max_drawdown_pct if c.com_dimensionamento else None,
          "retorno_base": c.sem_dimensionamento.total_return_pct if c.sem_dimensionamento else None,
          "retorno_dim": c.com_dimensionamento.total_return_pct if c.com_dimensionamento else None,
          "delta_drawdown": c.delta_drawdown, "delta_retorno": c.delta_retorno,
          "delta_exposicao_capital": c.delta_exposicao,
          "delta_exposicao_tempo": c.delta_exposicao_tempo,
          "delta_timing": c.delta_timing,
          "delta_operacoes": c.delta_operacoes, "delta_custo": c.delta_custo,
          "retorno_sem_custo_base": c.retorno_sem_custo_base,
          "retorno_sem_custo_dim": c.retorno_sem_custo_dim}
         for c in comparacoes],
    )


def cmd_barras():
    """H13 -- barras dirigidas por informacao (spec 026).

    Roda cada estrategia duas vezes sobre a MESMA base de 1h: uma agrupada por
    relogio, outra agrupada por atividade acumulada. As duas cobrem o mesmo
    intervalo de calendario e compartilham o mesmo buy-and-hold, que e o unico
    ponto fixo entre amostragens diferentes.

    O limiar NAO e parametrizavel: e calibrado ate a contagem de barras parear
    com a de tempo, consultando exclusivamente essa contagem. Expo-lo como flag
    convidaria a varre-lo ate um passar.
    """
    from rich import box
    from rich.table import Table

    from backtesting.barras import BASE_CANDLES, BASE_TIMEFRAME, run_barras_scan
    from utils.display import C_CYAN, C_DIM, C_LABEL, C_NEG, C_POS, console, header
    from utils.report_export import export_report

    tipos = None
    if len(sys.argv) > 2:
        pedido = sys.argv[2].lower()
        if pedido not in ("dollar", "cusum"):
            print(f"tipo invalido: {sys.argv[2]}; use dollar ou cusum")
            sys.exit(1)
        tipos = [pedido]

    header()
    console.print(f"[bold {C_CYAN}]barras dirigidas por informacao (H13)[/]")
    console.print(f"  [{C_DIM}]base {BASE_TIMEFRAME} x {BASE_CANDLES} candles; a versao de "
                  f"tempo e a MESMA base agrupada por relogio -- mesmo intervalo de "
                  f"calendario, mesmo buy-and-hold[/{C_DIM}]")
    console.print(f"  [{C_DIM}]limiar calibrado ate parear a contagem de barras; producao "
                  f"nao e tocada[/{C_DIM}]")
    console.print()

    comparacoes = run_barras_scan(tipos=tipos)

    ordem = {"melhora": 0, "so_na_busca": 1, "confundido": 2, "sem_vantagem": 3,
             "piora": 4, "inconclusivo": 5, "inerte": 6, "erro": 7}
    comparacoes.sort(key=lambda c: (ordem.get(c.status, 9), -c.delta_timing))
    conta = {k: sum(1 for c in comparacoes if c.status == k) for k in ordem}
    avaliadas = [c for c in comparacoes if c.status in
                 ("melhora", "so_na_busca", "confundido", "sem_vantagem", "piora")]

    console.print(f"  [{C_LABEL}]avaliadas[/] {len(avaliadas)}  "
                  f"[{C_POS}]melhora[/] {conta['melhora']}  "
                  f"[{C_CYAN}]so na busca[/] {conta['so_na_busca']}  "
                  f"[{C_CYAN}]confundidas[/] {conta['confundido']}  "
                  f"[{C_DIM}]sem vantagem[/] {conta['sem_vantagem']}  "
                  f"[{C_NEG}]piora[/] {conta['piora']}  "
                  f"[{C_DIM}]inconclusivas[/] {conta['inconclusivo']}  "
                  f"[{C_DIM}]inertes[/] {conta['inerte']}  "
                  f"[{C_DIM}]erro[/] {conta['erro']}")
    console.print()

    t = Table(box=box.SIMPLE_HEAD)
    for col in ("Estrategia", "Par", "Tipo"):
        t.add_column(col)
    for col in ("N tempo", "N barras", "DD tempo", "DD barras", "dDD",
                "Ret tempo", "Ret barras", "dRet", "dExpo", "dTiming",
                "Ops", "dCusto"):
        t.add_column(col, justify="right")
    t.add_column("Status")

    cores = {"melhora": C_POS, "piora": C_NEG, "inerte": C_DIM,
             "so_na_busca": C_CYAN, "confundido": C_CYAN}
    for c in comparacoes:
        cor = cores.get(c.status, C_DIM)
        rotulo = c.status.replace("_", " ")
        if c.tempo is None or c.barras is None:
            t.add_row(c.estrategia, c.par, c.tipo, *["-"] * 12,
                      f"[{cor}]{rotulo}[/{cor}]")
            continue
        medido = (c.retorno_sem_custo_tempo is not None
                  and c.retorno_sem_custo_barras is not None)
        t.add_row(
            c.estrategia, c.par, c.tipo,
            str(c.n_tempo), str(c.n_barras),
            f"{c.tempo.max_drawdown_pct:.2f}", f"{c.barras.max_drawdown_pct:.2f}",
            f"{c.delta_drawdown:+.2f}",
            f"{c.tempo.total_return_pct:.2f}", f"{c.barras.total_return_pct:.2f}",
            f"{c.delta_retorno:+.2f}",
            f"{c.delta_exposicao:+.1f}", f"{c.delta_timing:+.2f}",
            f"{c.tempo.total_trades}/{c.barras.total_trades}",
            f"{c.delta_custo:+.2f}" if medido else "-",
            f"[{cor}]{rotulo}[/{cor}]",
        )
    console.print(t)
    console.print()

    # Diagnostico da reamostragem (T038). E o numero que distingue "nao houve
    # vantagem" de "o instrumento nao mediu nada" -- H12 so descobriu que 37 de
    # 48 combinacoes eram inertes ao confrontar o fator medio com o previsto.
    com_barras = [c for c in comparacoes if c.n_barras > 0]
    if com_barras:
        console.print(f"  [bold {C_CYAN}]diagnostico da reamostragem[/]")
        for tipo in sorted({c.tipo for c in com_barras}):
            do_tipo = [c for c in com_barras if c.tipo == tipo]
            pct = sorted(c.pct_barras_1_candle for c in do_tipo)
            razao = sorted(c.n_barras / c.n_base for c in do_tipo if c.n_base)
            console.print(
                f"    [{C_LABEL}]{tipo}[/] {len(do_tipo)} combinacoes: "
                f"barras por candle de base, mediana {razao[len(razao) // 2]:.3f}; "
                f"barras de 1 candle, mediana {pct[len(pct) // 2]:.1f}%")
        console.print()

    console.print(f"  [{C_DIM}]\"inerte\": cada candle de base virou uma barra -- as duas "
                  f"versoes sao a mesma serie, nada foi medido[/{C_DIM}]")
    console.print(f"  [{C_DIM}]\"confundido\": a versao de tempo PERDE dinheiro, entao operar "
                  f"menos aproxima de zero -- o limite dessa logica e nao operar[/{C_DIM}]")
    console.print(f"  [{C_DIM}]\"so na busca\" NAO e aprovacao: melhorou onde foi medido e nao "
                  f"se sustentou na validacao fora da amostra[/{C_DIM}]")
    console.print(f"  [{C_DIM}]\"inconclusivo\": amostra insuficiente ou aquecimento que nao "
                  f"cabe na janela -- nao e ausencia de vantagem[/{C_DIM}]")
    console.print(f"  [{C_DIM}]dTiming desconta a exposicao de TEMPO, a grandeza que este "
                  f"mecanismo move (D4) -- e ele, nao dRet, que separa habilidade de "
                  f"menor participacao[/{C_DIM}]")

    com_custo = [c for c in avaliadas if c.retorno_sem_custo_tempo is not None
                 and c.retorno_sem_custo_barras is not None]
    if com_custo:
        n = len(com_custo)
        d_ret = sum(c.delta_retorno for c in com_custo) / n
        d_sem = sum(c.retorno_sem_custo_barras - c.retorno_sem_custo_tempo
                    for c in com_custo) / n
        d_custo = sum(c.delta_custo for c in com_custo) / n
        d_ops = sum(c.delta_operacoes for c in com_custo) / n
        console.print()
        console.print(f"  [{C_LABEL}]custo de giro[/] em {n} comparacoes: "
                      f"dRet medio {d_ret:+.2f}pp, dRet sem custo {d_sem:+.2f}pp, "
                      f"diferenca atribuivel a custo {d_custo:+.2f}pp, "
                      f"dOperacoes medio {d_ops:+.1f}")

    console.print()
    console.print(f"  [{C_DIM}]executabilidade (D6): seria executavel -- e aritmetica sobre "
                  f"candles que o bot ja busca. RESSALVA: o limiar e calibrado em historico "
                  f"e regimes de volume mudam; operar exigiria recalibracao periodica, "
                  f"mecanismo que esta spec NAO implementa[/{C_DIM}]")

    export_report(
        "barras",
        {"base_timeframe": BASE_TIMEFRAME, "base_candles": BASE_CANDLES,
         "tipos": sorted({c.tipo for c in comparacoes}),
         "pares": len({c.par for c in comparacoes}),
         "estrategias": sorted({c.estrategia for c in comparacoes})},
        [{"estrategia": c.estrategia, "par": c.par, "tipo": c.tipo,
          "status": c.status, "motivo": c.motivo,
          "n_base": c.n_base, "n_tempo": c.n_tempo, "n_barras": c.n_barras,
          "dias_janela": c.dias_janela,
          "aquecimento_dias_tempo": c.aquecimento_dias_tempo,
          "aquecimento_dias_barras": c.aquecimento_dias_barras,
          "pct_barras_1_candle": c.pct_barras_1_candle,
          "limiar_calibrado": c.limiar_calibrado,
          "drawdown_tempo": c.tempo.max_drawdown_pct if c.tempo else None,
          "drawdown_barras": c.barras.max_drawdown_pct if c.barras else None,
          "retorno_tempo": c.tempo.total_return_pct if c.tempo else None,
          "retorno_barras": c.barras.total_return_pct if c.barras else None,
          "buy_hold_tempo": c.tempo.buy_hold_return_pct if c.tempo else None,
          "buy_hold_barras": c.barras.buy_hold_return_pct if c.barras else None,
          "delta_drawdown": c.delta_drawdown, "delta_retorno": c.delta_retorno,
          "delta_exposicao": c.delta_exposicao, "delta_timing": c.delta_timing,
          "delta_timing_validacao": c.delta_timing_validacao,
          "delta_operacoes": c.delta_operacoes, "delta_custo": c.delta_custo,
          "retorno_sem_custo_tempo": c.retorno_sem_custo_tempo,
          "retorno_sem_custo_barras": c.retorno_sem_custo_barras}
         for c in comparacoes],
    )


def cmd_modelo():
    """H14 -- classificador sobre rotulos de barreira tripla (spec 027).

    Nenhum argumento, diferente de `volatilidade [ALVO]` e `barras [TIPO]`:
    barreiras, atributos, limiar de correlacao, embargo e universo sao todos
    declarados em research.md e fixos. Um modelo tem eixos demais para expor
    qualquer um com seguranca -- H13 obteve 1 aprovacao em 96 testes.
    """
    from rich import box
    from rich.table import Table

    from backtesting.modelo import (
        MARGEM_VS_EMBARALHADO_PP,
        limiar_de_decisao,
        limiar_de_empate,
        resumo_agregado,
        run_modelo_scan,
    )
    from strategy.barreira_tripla import ATRIBUTOS, ParametrosBarreira
    from utils.display import C_CYAN, C_DIM, C_LABEL, C_NEG, C_POS, console, header
    from utils.report_export import export_report

    p = ParametrosBarreira()
    header()
    console.print(f"[bold {C_CYAN}]classificador sobre barreira tripla (H14)[/]")
    console.print(f"  [{C_DIM}]barreiras: stop {p.sl_mult}xATR, alvo {p.tp_mult}xATR, "
                  f"limite {p.limite_velas} velas | embargo {p.limite_velas} velas[/{C_DIM}]")
    console.print(f"  [{C_DIM}]atributos declarados ({len(ATRIBUTOS)}): "
                  f"{', '.join(ATRIBUTOS)}[/{C_DIM}]")
    console.print(f"  [{C_LABEL}]limiar de decisao[/] {limiar_de_decisao():.4f} "
                  f"(probabilidade de alvo) — [{C_LABEL}]razao de empate[/] "
                  f"{limiar_de_empate():.3f} (alvo/stop)")
    console.print(f"  [{C_DIM}]os dois caem das barreiras, nao sao ajustaveis; producao "
                  f"nao e tocada[/{C_DIM}]")
    console.print()

    avaliacoes = run_modelo_scan()

    ordem = {"melhora": 0, "so_na_busca": 1, "insuficiente": 2, "confundido": 3,
             "sem_vantagem": 4, "piora": 5, "sem_sinal": 6, "inconclusivo": 7,
             "classe_unica": 8, "nao_convergiu": 9, "erro": 10}
    avaliacoes.sort(key=lambda a: (ordem.get(a.status, 99), -a.delta_vs_embaralhado))
    conta = {k: sum(1 for a in avaliacoes if a.status == k) for k in ordem}

    console.print(f"  [{C_POS}]melhora[/] {conta['melhora']}  "
                  f"[{C_CYAN}]so na busca[/] {conta['so_na_busca']}  "
                  f"[{C_CYAN}]insuficientes[/] {conta['insuficiente']}  "
                  f"[{C_CYAN}]confundidas[/] {conta['confundido']}  "
                  f"[{C_DIM}]sem vantagem[/] {conta['sem_vantagem']}  "
                  f"[{C_NEG}]piora[/] {conta['piora']}  "
                  f"[{C_DIM}]sem sinal[/] {conta['sem_sinal']}  "
                  f"[{C_DIM}]inconclusivas[/] {conta['inconclusivo']}  "
                  f"[{C_DIM}]nao convergiu[/] {conta['nao_convergiu']}  "
                  f"[{C_DIM}]erro[/] {conta['erro']}")
    console.print()

    t = Table(box=box.SIMPLE_HEAD)
    t.add_column("Par")
    for col in ("Treino", "Teste", "Decid.", "Razao ger", "Razao dec",
                "Ops mod", "Ops reg", "dRet", "dTiming", "vs emb"):
        t.add_column(col, justify="right")
    t.add_column("Status")

    cores = {"melhora": C_POS, "piora": C_NEG, "so_na_busca": C_CYAN,
             "insuficiente": C_CYAN, "confundido": C_CYAN}
    for a in avaliacoes:
        m = a.modelo
        cor = cores.get(a.status, C_DIM)
        rotulo = a.status.replace("_", " ")
        if m is None:
            t.add_row(a.par, *["-"] * 10, f"[{cor}]{rotulo}[/{cor}]")
            continue
        rg = m.razao_chances_geral
        rd = m.razao_chances_decidido
        ops_m = m.backtest.total_trades if m.backtest else 0
        ops_r = a.regras.total_trades if a.regras else 0
        t.add_row(
            a.par, str(m.n_treino), str(m.n_teste), str(m.n_decidido),
            f"{rg:.3f}" if rg is not None else "-",
            f"{rd:.3f}" if rd is not None else "-",
            str(ops_m), str(ops_r),
            f"{a.delta_retorno:+.2f}", f"{a.delta_timing:+.2f}",
            f"{a.delta_vs_embaralhado:+.2f}",
            f"[{cor}]{rotulo}[/{cor}]",
        )
    console.print(t)
    console.print()

    # RESPOSTA AGREGADA -- a unidade natural de avaliacao de um modelo global.
    # Por par, a linha de base de regras faz 1 a 9 operacoes na janela de teste
    # e tudo cai em `inconclusivo` por amostra; o conjunto responde.
    r = resumo_agregado(avaliacoes, p)
    mod, emb = r["modelo"], r["embaralhado"]
    console.print(f"  [bold {C_CYAN}]resposta agregada[/] "
                  f"[{C_DIM}]({r['n_pares']} pares; o modelo e unico e treinado "
                  f"sobre os pares agrupados, entao o conjunto e a unidade de "
                  f"avaliacao)[/{C_DIM}]")
    console.print(f"    [{C_LABEL}]operacoes[/] modelo {r['trades']['modelo']} | "
                  f"embaralhado {r['trades']['embaralhado']} | "
                  f"regras {r['trades']['regras']}")
    console.print(f"    [{C_LABEL}]modelo[/]       alvo {mod['alvo']} / stop "
                  f"{mod['stop']} -> razao "
                  f"{mod['razao']:.4f}" if mod['razao'] is not None else
                  f"    [{C_LABEL}]modelo[/] sem decisoes")
    if emb["razao"] is not None:
        console.print(f"    [{C_LABEL}]embaralhado[/]  alvo {emb['alvo']} / stop "
                      f"{emb['stop']} -> razao {emb['razao']:.4f}")
    else:
        console.print(f"    [{C_LABEL}]embaralhado[/]  decide ZERO vezes "
                      f"[{C_DIM}]— correto: sem relacao atributo-rotulo a melhor "
                      f"previsao e a taxa base, abaixo do limiar de decisao[/{C_DIM}]")
    ponto = r.get("supera_empate_pontual")
    console.print(f"    [{C_LABEL}]supera o empate?[/] "
                  f"{'SIM' if r['supera_empate'] else 'NAO'} "
                  f"[{C_DIM}](pela estimativa pontual: "
                  f"{'sim' if ponto else 'nao'})[/{C_DIM}]")
    console.print()

    # Diagnostico de purga (US2 no relatorio).
    purg = [a for a in avaliacoes if a.n_purgadas or a.n_embargadas]
    if purg:
        console.print(f"  [bold {C_CYAN}]purga[/] "
                      f"{purg[0].n_purgadas} amostras removidas por sobreposicao de "
                      f"horizonte, {purg[0].n_embargadas} pelo embargo "
                      f"[{C_DIM}](temporal e GLOBAL entre pares: purgar par a par "
                      f"deixaria o desfecho de um par no treino enquanto outro, "
                      f"correlacionado a 0,71, esta no teste)[/{C_DIM}]")
        console.print()

    console.print(f"  [{C_DIM}]\"sem sinal\": nao se distingue do modelo de rotulos "
                  f"EMBARALHADOS (margem {MARGEM_VS_EMBARALHADO_PP:.1f}pp) -- o que se "
                  f"mediu foi ajuste a ruido[/{C_DIM}]")
    console.print(f"  [{C_DIM}]\"insuficiente\": ha sinal, e ele NAO paga as barreiras "
                  f"-- razao de chances nao supera o empate alem da incerteza[/{C_DIM}]")
    console.print(f"  [{C_DIM}]\"confundido\": as regras perdem dinheiro, entao operar "
                  f"menos aproxima de zero e isso nao e vantagem[/{C_DIM}]")
    console.print(f"  [{C_DIM}]ACURACIA NAO APARECE de proposito: prever sempre \"stop\" "
                  f"acerta 62,8% e nunca opera. a metrica e a razao de chances no "
                  f"subconjunto DECIDIDO[/{C_DIM}]")
    console.print(f"  [{C_DIM}]o limiar usa o limite inferior do intervalo de confianca, "
                  f"nao a estimativa pontual: comparar o ponto converte ruido em "
                  f"aprovacao[/{C_DIM}]")
    console.print()
    console.print(f"  [{C_DIM}]executabilidade (D6): avaliar o modelo por ciclo e barato, "
                  f"mas NAO existe mecanismo de retreino nem de deteccao de degradacao, "
                  f"e aqui a degradacao e silenciosa -- o modelo segue emitindo "
                  f"probabilidades normais enquanto a relacao aprendida morre[/{C_DIM}]")

    export_report(
        "modelo",
        {"sl_mult": p.sl_mult, "tp_mult": p.tp_mult,
         "limite_velas": p.limite_velas, "atributos": ATRIBUTOS,
         "limiar_decisao": limiar_de_decisao(), "razao_empate": limiar_de_empate(),
         "margem_vs_embaralhado_pp": MARGEM_VS_EMBARALHADO_PP,
         "agregado": r},
        [{"par": a.par, "status": a.status, "motivo": a.motivo,
          "n_purgadas": a.n_purgadas, "n_embargadas": a.n_embargadas,
          "n_treino": a.modelo.n_treino if a.modelo else None,
          "n_teste": a.modelo.n_teste if a.modelo else None,
          "n_decidido": a.modelo.n_decidido if a.modelo else None,
          "n_alvo_decidido": a.modelo.n_alvo_decidido if a.modelo else None,
          "n_stop_decidido": a.modelo.n_stop_decidido if a.modelo else None,
          "razao_geral": a.modelo.razao_chances_geral if a.modelo else None,
          "razao_decidido": a.modelo.razao_chances_decidido if a.modelo else None,
          "convergiu": a.modelo.convergiu if a.modelo else None,
          "coeficientes": a.modelo.coeficientes if a.modelo else None,
          "dist_classes": a.modelo.dist_classes if a.modelo else None,
          "retorno_modelo": a.modelo.backtest.total_return_pct
                            if (a.modelo and a.modelo.backtest) else None,
          "retorno_regras": a.regras.total_return_pct if a.regras else None,
          "ops_modelo": a.modelo.backtest.total_trades
                        if (a.modelo and a.modelo.backtest) else None,
          "ops_regras": a.regras.total_trades if a.regras else None,
          "delta_retorno": a.delta_retorno, "delta_timing": a.delta_timing,
          "delta_vs_embaralhado": a.delta_vs_embaralhado,
          "delta_custo": a.delta_custo,
          "retorno_sem_custo_modelo": a.retorno_sem_custo_modelo,
          "retorno_sem_custo_regras": a.retorno_sem_custo_regras}
         for a in avaliacoes],
    )


def cmd_arbitragem():
    """H15 -- arbitragem entre corretoras (spec 029).

    Instrumento de amostragem, nao veredito: mede o diferencial liquido
    entre seis corretoras publicas para um par, sem enviar ordem alguma e
    sem exigir chave de API. O veredito exige amostra acumulada ao longo do
    tempo (Assumptions da spec) -- esta execucao mede um ciclo e persiste.
    """
    from datetime import datetime

    from rich import box
    from rich.table import Table

    from backtesting.arbitragem import CORRETORAS, MIN_OBSERVACOES_AGREGACAO, VOLUME_USDT_PADRAO, agregar, medir_ciclo
    from data.arbitragem_store import carregar_observacoes
    from utils.display import C_CYAN, C_DIM, C_LABEL, C_NEG, C_POS, console, header
    from utils.report_export import export_report

    par = sys.argv[2] if len(sys.argv) > 2 else "BTC/USDT"

    header()
    console.print(f"[bold {C_CYAN}]arbitragem entre corretoras (H15)[/]")
    console.print(f"  [{C_DIM}]{par} em {len(CORRETORAS)} corretoras publicas, "
                  f"volume de US$ {VOLUME_USDT_PADRAO:,.0f} por perna -- "
                  f"nenhuma ordem enviada, producao intocada[/{C_DIM}]")
    console.print(f"  [{C_DIM}]cotacao: {par.split('/')[1]} -- comparacoes entre cotacoes "
                  f"diferentes sao recusadas, nunca incluidas[/{C_DIM}]")
    console.print()

    comparacoes, indisponiveis, pares_recusados = medir_ciclo(par)

    if indisponiveis:
        console.print(f"  [{C_NEG}]corretoras indisponiveis neste ciclo[/]: {', '.join(indisponiveis)}")
        console.print()

    if pares_recusados:
        console.print(f"  [{C_NEG}]pares recusados (cotacao diferente)[/]:")
        for corretora_a, corretora_b, motivo in pares_recusados:
            console.print(f"    [{C_DIM}]{corretora_a} x {corretora_b}: {motivo}[/{C_DIM}]")
        console.print()

    cores = {"oportunidade": C_POS, "sem_oportunidade": C_DIM,
             "custo_desconhecido": C_CYAN, "profundidade_insuficiente": C_CYAN,
             "latencia_alta": C_CYAN}

    t = Table(box=box.SIMPLE_HEAD)
    for col in ("Compra", "Venda"):
        t.add_column(col)
    for col in ("Bruto %", "Custo %", "Liquido %", "Volume US$", "Intervalo ms"):
        t.add_column(col, justify="right")
    t.add_column("Estado")

    for c in comparacoes:
        cor = cores.get(c.estado, C_DIM)
        custo_fmt = f"{c.custo_pct * 100:.3f}" if c.custo_pct is not None else "-"
        liquido_fmt = f"{c.diferencial_liquido_pct * 100:+.3f}" if c.diferencial_liquido_pct is not None else "-"
        t.add_row(
            c.corretora_compra, c.corretora_venda,
            f"{c.diferencial_bruto_pct * 100:+.4f}", custo_fmt, liquido_fmt,
            f"{c.volume_preenchido_usdt:,.0f}", f"{c.intervalo_ms:.0f}",
            f"[{cor}]{c.estado.replace('_', ' ')}[/{cor}]",
        )
    console.print(t)
    console.print()

    historico = carregar_observacoes()
    relatorio = agregar(comparacoes, indisponiveis, pares_recusados, historico)

    console.print(f"  [bold {C_CYAN}]agregado historico[/]")
    if relatorio.periodo_coberto:
        inicio = datetime.fromtimestamp(relatorio.periodo_coberto[0]).strftime("%Y-%m-%d %H:%M:%S")
        fim = datetime.fromtimestamp(relatorio.periodo_coberto[1]).strftime("%Y-%m-%d %H:%M:%S")
        console.print(f"    [{C_LABEL}]periodo[/]: {inicio} -- {fim}")
    console.print(f"    [{C_LABEL}]N total[/]: {relatorio.n_observacoes_total}")
    for (corretora_a, corretora_b), n in sorted(relatorio.n_observacoes_por_combinacao.items()):
        console.print(f"      [{C_DIM}]{corretora_a} x {corretora_b}: {n}[/{C_DIM}]")
    if relatorio.estado_agregado == "inconclusivo":
        maior = max(relatorio.n_observacoes_por_combinacao.values(), default=0)
        console.print(f"    [{C_CYAN}]inconclusivo[/] -- faltam "
                       f"{max(0, MIN_OBSERVACOES_AGREGACAO - maior)} observacoes na combinacao "
                       f"mais medida para atingir o minimo declarado ({MIN_OBSERVACOES_AGREGACAO})")
    else:
        console.print(f"    [{C_POS}]amostra suficiente[/] -- so descritivo, "
                       f"NAO e veredito de aprovacao/reprovacao (Assumptions da spec)")
    console.print()

    console.print(f"  [{C_LABEL}]executabilidade (D6)[/]: [{C_NEG}]inexecutavel hoje[/] -- "
                  f"{relatorio.motivo_executabilidade}")

    export_report(
        "arbitragem",
        {"par": par, "corretoras": list(CORRETORAS), "volume_usdt": VOLUME_USDT_PADRAO,
         "indisponiveis": indisponiveis, "n_observacoes_total": relatorio.n_observacoes_total,
         "estado_agregado": relatorio.estado_agregado, "periodo_coberto": relatorio.periodo_coberto},
        [{"corretora_compra": c.corretora_compra, "corretora_venda": c.corretora_venda,
          "diferencial_bruto_pct": c.diferencial_bruto_pct, "custo_pct": c.custo_pct,
          "diferencial_liquido_pct": c.diferencial_liquido_pct,
          "volume_preenchido_usdt": c.volume_preenchido_usdt,
          "intervalo_ms": c.intervalo_ms, "estado": c.estado}
         for c in comparacoes],
    )


def cmd_onchain():
    """H17 -- sinais on-chain, comparacao isolada BTC-only (spec 034).

    NAO e um veredito de aprovacao/reprovacao -- compara, sobre o mesmo
    par (BTC/USDT, unica cobertura da fonte de dados, spec 033) e mesmo
    periodo, o modelo original de H14 contra o modelo com o atributo
    on-chain a mais, reusando a bateria de avaliacao ja existente sem
    alterar criterio.
    """
    from rich import box
    from rich.table import Table

    from backtesting.onchain_hipotese import avaliar_h17
    from utils.display import C_CYAN, C_DIM, C_LABEL, C_NEG, C_POS, console, header
    from utils.report_export import export_report

    header()
    console.print(f"[bold {C_CYAN}]sinais on-chain (H17)[/]")
    console.print(f"  [{C_DIM}]BTC/USDT -- unica cobertura da fonte de dados (spec 033); "
                  f"comparacao isolada contra o mesmo par/periodo, nunca contra o resultado "
                  f"pooled de 12 pares ja publicado por H14[/{C_DIM}]")
    console.print()

    relatorio = avaliar_h17()

    console.print(f"  [{C_LABEL}]atributo declarado[/]: {relatorio.atributo_declarado}")
    console.print(f"  [{C_LABEL}]colinearidade contra os 5 atributos de H14[/]:")
    for nome, valor in sorted(relatorio.correlacao_onchain.items()):
        console.print(f"    [{C_DIM}]{nome}: {valor:+.3f}[/{C_DIM}]")
    console.print()

    t = Table(box=box.SIMPLE_HEAD)
    t.add_column("Avaliacao")
    for col in ("n_treino", "n_teste", "razao geral", "razao decidido"):
        t.add_column(col, justify="right")
    t.add_column("Estado")

    cores = {"melhora": C_POS, "piora": C_NEG}
    for nome, a in (("sem on-chain", relatorio.avaliacao_base),
                    ("com on-chain", relatorio.avaliacao_onchain)):
        cor = cores.get(a.status, C_DIM)
        m = a.modelo
        t.add_row(
            nome,
            str(m.n_treino) if m else "-",
            str(m.n_teste) if m else "-",
            f"{m.razao_chances_geral:.3f}" if m and m.razao_chances_geral is not None else "-",
            f"{m.razao_chances_decidido:.3f}" if m and m.razao_chances_decidido is not None else "-",
            f"[{cor}]{a.status}[/{cor}]" + (f" ({a.motivo})" if a.motivo else ""),
        )
    console.print(t)
    console.print()

    console.print(f"  [{C_DIM}]nenhum veredito de aprovacao/reprovacao aqui -- compara a "
                  f"razao de chances com e sem o atributo, mesmos eventos. Nenhuma ordem "
                  f"enviada, producao intocada[/{C_DIM}]")

    def _serializar(a):
        m = a.modelo
        return {
            "status": a.status, "motivo": a.motivo,
            "n_treino": m.n_treino if m else None, "n_teste": m.n_teste if m else None,
            "razao_geral": m.razao_chances_geral if m else None,
            "razao_decidido": m.razao_chances_decidido if m else None,
        }

    export_report(
        "onchain",
        {"par": "BTC/USDT", "atributo": relatorio.atributo_declarado,
         "correlacao": relatorio.correlacao_onchain},
        [{"avaliacao": "sem_onchain", **_serializar(relatorio.avaliacao_base)},
         {"avaliacao": "com_onchain", **_serializar(relatorio.avaliacao_onchain)}],
    )


COMMANDS = {
    "backtest":      cmd_backtest,
    "edge":          cmd_edge,
    "multibacktest": cmd_multibacktest,
    "scan":          cmd_scan,
    "compare":       cmd_comparar,
    "multimarket":   cmd_multimarket,
    "horizonte":     cmd_horizonte,
    "horizontes":    cmd_horizonte,
    "volatilidade":  cmd_volatilidade,
    "voltarget":     cmd_volatilidade,
    "barras":        cmd_barras,
    "bars":          cmd_barras,
    "modelo":        cmd_modelo,
    "ml":            cmd_modelo,
    "arbitragem":    cmd_arbitragem,
    "onchain":       cmd_onchain,
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
