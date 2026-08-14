from dataclasses import dataclass
from typing import List, Optional, Tuple

import pandas as pd

from backtesting.engine import BacktestResult, print_report, precompute_signals, simulate_backtest
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

# Criterios de aprovacao automatica (ROADMAP.md, esbocado na Fase 1), aplicados
# sobre a janela de validacao out-of-sample, nunca sobre a de treino.
MIN_TRADES_FOR_APPROVAL = 10
MIN_PROFIT_FACTOR_FOR_APPROVAL = 1.2
MAX_ACCEPTABLE_DRAWDOWN_PCT = 10.0


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


@dataclass
class ValidationVerdict:
    status: str  # "aprovado" | "reprovado" | "inconclusivo"
    reasons: List[str]


def evaluate_validation(
    result: Optional[BacktestResult],
    min_trades: int = MIN_TRADES_FOR_APPROVAL,
    min_profit_factor: float = MIN_PROFIT_FACTOR_FOR_APPROVAL,
    max_drawdown_pct: float = MAX_ACCEPTABLE_DRAWDOWN_PCT,
) -> ValidationVerdict:
    """Aplica os criterios de aprovacao automatica sobre a janela de validacao
    out-of-sample (nunca sobre a de treino -- SC-005/spec US3)."""
    if result is None:
        return ValidationVerdict(
            status="inconclusivo",
            reasons=["dados insuficientes para uma janela de validacao out-of-sample"],
        )

    reasons: List[str] = []
    if result.total_trades < min_trades:
        reasons.append(f"apenas {result.total_trades} trades na validacao (minimo {min_trades})")
    if result.total_return_pct <= result.buy_hold_return_pct:
        reasons.append(
            f"retorno {result.total_return_pct:+.2f}% nao supera buy-and-hold "
            f"{result.buy_hold_return_pct:+.2f}%"
        )
    if result.profit_factor <= min_profit_factor:
        reasons.append(f"profit factor {result.profit_factor:.2f} abaixo do minimo {min_profit_factor}")
    if result.max_drawdown_pct > max_drawdown_pct:
        reasons.append(f"drawdown {result.max_drawdown_pct:.2f}% acima do aceitavel {max_drawdown_pct:.0f}%")

    if reasons:
        return ValidationVerdict(status="reprovado", reasons=reasons)
    return ValidationVerdict(status="aprovado", reasons=[])


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

    console.print()
    verdict_color = {"aprovado": C_POS, "reprovado": C_NEG, "inconclusivo": C_CYAN}[verdict.status]
    console.print(f"[bold {verdict_color}]VEREDITO: {verdict.status.upper()}[/]")
    log.info(f"\nVEREDITO: {verdict.status.upper()}")
    for reason in verdict.reasons:
        console.print(f"[{C_NEG}]  - {reason}[/]")
        log.info(f"  - {reason}")
