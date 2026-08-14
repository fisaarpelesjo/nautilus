from typing import Optional, Tuple

import pandas as pd

from backtesting.approval import ApprovalVerdict, diagnose_profile, evaluate_approval
from backtesting.engine import BacktestResult, edge_score_band, print_report, precompute_signals, simulate_backtest
from data.fetcher import fetch_ohlcv
from strategy.ema_rsi import EmaRsiStrategy
from utils.display import C_CYAN, C_NEG, C_POS, console
from utils.logger import get_logger

log = get_logger("backtest")

# Janela minima (candles) exigida em CADA fatia para o split ser considerado valido.
# Cobre o warmup de indicadores (EMA50 exige ~50 candles) mais uma margem para que
# um numero minimo de trades tenha chance real de ocorrer.
MIN_WINDOW_CANDLES = 150
DEFAULT_VALIDATION_RATIO = 0.3

# Alias de compatibilidade -- a logica de veredito foi generalizada e movida para
# backtesting/approval.py (spec 002), reusada por multibacktest/scan/edge alem do
# fluxo out-of-sample daqui.
ValidationVerdict = ApprovalVerdict
evaluate_validation = evaluate_approval


def split_train_validation(
    df: pd.DataFrame,
    validation_ratio: float = DEFAULT_VALIDATION_RATIO,
    min_window_candles: int = MIN_WINDOW_CANDLES,
) -> Tuple[pd.DataFrame, Optional[pd.DataFrame]]:
    """Divide candles em fatias contiguas e nao sobrepostas (sem embaralhar --
    dado e serie temporal): treino (inicio) + validacao out-of-sample (fim).

    Se qualquer fatia ficar menor que `min_window_candles`, o split e considerado
    invalido e o dataframe inteiro volta como treino, sem janela de validacao.
    """
    split_idx = int(len(df) * (1 - validation_ratio))
    train = df.iloc[:split_idx]
    validation = df.iloc[split_idx:]

    if len(train) < min_window_candles or len(validation) < min_window_candles:
        return df, None

    return train, validation


def run_backtest_with_validation(
    symbol: str,
    timeframe: str,
    validation_ratio: float = DEFAULT_VALIDATION_RATIO,
    initial_capital: float = 1000.0,
    candle_limit: int = 2000,
) -> Tuple[BacktestResult, Optional[BacktestResult], ValidationVerdict]:
    df = fetch_ohlcv(symbol, timeframe, limit=candle_limit)
    strategy = EmaRsiStrategy()
    df = strategy.calculate_indicators(df)

    # Sinais calculados uma unica vez sobre o df inteiro (antes do split) e so
    # depois fatiados -- se calculados por fatia, o .shift(1) usado para detectar
    # cruzamento de EMA fica sem contexto no primeiro candle da fatia de validacao
    # (viraria NaN), perdendo um cruzamento real que caia exatamente na fronteira.
    signals = precompute_signals(df, strategy)

    train_df, validation_df = split_train_validation(df, validation_ratio)

    train_result = simulate_backtest(
        train_df, strategy, initial_capital=initial_capital,
        precomputed_signals=signals.loc[train_df.index],
    )

    validation_result = None
    if validation_df is not None:
        # start_index=0: os indicadores ja foram calculados sobre o df completo
        # antes do split, entao a fatia de validacao nao carrega NaN de warmup --
        # descartar candles aqui so encolheria ainda mais a menor das duas janelas.
        validation_result = simulate_backtest(
            validation_df, strategy, initial_capital=initial_capital,
            start_index=0, precomputed_signals=signals.loc[validation_df.index],
        )

    verdict = evaluate_validation(validation_result)
    _print_validation_report(train_result, validation_result, verdict)
    return train_result, validation_result, verdict


def _print_validation_report(
    train_result: BacktestResult,
    validation_result: Optional[BacktestResult],
    verdict: ValidationVerdict,
) -> None:
    console.print()
    console.print(f"[bold {C_CYAN}]TREINO / OTIMIZACAO[/]")
    log.info("\nTREINO / OTIMIZACAO")
    print_report(train_result)

    console.print()
    console.print(f"[bold {C_CYAN}]VALIDACAO OUT-OF-SAMPLE[/]")
    log.info("\nVALIDACAO OUT-OF-SAMPLE")
    if validation_result is None:
        msg = "dados insuficientes para uma janela de validacao out-of-sample -- veredito inconclusivo"
        console.print(f"[{C_NEG}]{msg}[/]")
        log.info(msg)
    else:
        print_report(validation_result)

    edge_score = validation_result.edge_score if validation_result is not None else None
    _print_verdict(verdict, edge_score=edge_score)


def run_edge_report(
    symbol: str,
    timeframe: str,
    initial_capital: float = 1000.0,
    candle_limit: int = 2000,
) -> Tuple[BacktestResult, ApprovalVerdict]:
    """Roda um backtest de janela unica (sem split treino/validacao -- isso e
    `backtest --validate`) e calcula o veredito de aprovacao sobre o resultado
    inteiro. Usado por `python main.py edge`, que ate esta spec era um alias
    literal de `backtest`."""
    df = fetch_ohlcv(symbol, timeframe, limit=candle_limit)
    strategy = EmaRsiStrategy()
    df = strategy.calculate_indicators(df)

    result = simulate_backtest(df, strategy, initial_capital=initial_capital)
    verdict = evaluate_approval(result)
    diagnosis = diagnose_profile(result) if verdict.status == "reprovado" else None

    print_report(result)
    _print_verdict(verdict, diagnosis, edge_score=result.edge_score)
    return result, verdict


def _print_verdict(
    verdict: ApprovalVerdict,
    diagnosis: Optional[str] = None,
    edge_score: Optional[float] = None,
) -> None:
    console.print()
    verdict_color = {"aprovado": C_POS, "reprovado": C_NEG, "inconclusivo": C_CYAN}[verdict.status]
    console.print(f"[bold {verdict_color}]VEREDITO: {verdict.status.upper()}[/]")
    log.info(f"\nVEREDITO: {verdict.status.upper()}")
    for reason in verdict.reasons:
        console.print(f"[{C_NEG}]  - {reason}[/]")
        log.info(f"  - {reason}")
    if diagnosis:
        console.print(f"[{C_CYAN}]  {diagnosis}[/]")
        log.info(f"  {diagnosis}")
    if edge_score is not None:
        band = edge_score_band(edge_score)
        console.print(f"[{C_CYAN}]  edge score: {edge_score:+.2f} ({band})[/]")
        log.info(f"  edge score: {edge_score:+.2f} ({band})")
