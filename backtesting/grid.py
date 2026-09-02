"""H18 -- grid trading com gestao de cauda (spec 035).

Reusa o motor de metricas ja existente (Trade/BacktestResult/
_calculate_advanced_metrics, backtesting/engine.py) e o criterio de
aprovacao ja existente (evaluate_approval/edge_score, backtesting/
approval.py) -- sem inventar nenhum dos dois (FR-006).

A gestao de cauda que a objecao original de H18 apontava como ausente e o
classificador de regime ja existente (strategy/ema_rsi.py, ADX): a grade
so abre em regime "sideways" e liquida tudo a mercado quando o regime vira
"trending" (FR-002/FR-003).
"""

from dataclasses import dataclass
from typing import List, Optional

import numpy as np
import pandas as pd

from backtesting.engine import BacktestResult, Trade, _buy_hold_return_pct, _calculate_advanced_metrics
from config.settings import BACKTEST_FEE_RATE, BACKTEST_SLIPPAGE_PCT, MIN_PRICE_USDT
from utils.logger import get_logger

log = get_logger("grid")

EXIT_REASON_GRID = "grid"
EXIT_REASON_REGIME = "regime mudou para trending"


@dataclass
class ParametrosGrade:
    n_niveis: int = 10
    capital_inicial: float = 1000.0


@dataclass
class NivelGrade:
    preco_compra: float
    preco_venda: float
    ocupado: bool = False
    preco_entrada_ajustado: float = 0.0
    instante_entrada: object = None


def _criar_niveis(bb_lower: float, bb_upper: float, n_niveis: int) -> List[NivelGrade]:
    fronteiras = np.linspace(bb_lower, bb_upper, n_niveis + 1)
    return [NivelGrade(preco_compra=fronteiras[i], preco_venda=fronteiras[i + 1]) for i in range(n_niveis)]


def simular_grade(
    df: pd.DataFrame,
    params: Optional[ParametrosGrade] = None,
    fee_rate: float = BACKTEST_FEE_RATE,
    slippage_pct: float = BACKTEST_SLIPPAGE_PCT,
) -> BacktestResult:
    """Simula uma grade sobre `df` (MUST ja ter `bb_lower`/`bb_upper`/
    `regime` calculados, mesmas colunas de `strategy/ema_rsi.py`).

    Mecanica (D3, research.md): por candle, cada nivel processa NO MAXIMO
    uma transicao -- se ocupado, checa venda primeiro; senao, checa compra.
    Um nivel que vende num candle nao recompra no mesmo candle. Liquidacao
    forcada (D4): regime "trending" com niveis ocupados fecha TUDO ao
    `close` do candle, gestao de cauda desta hipotese (FR-003).
    """
    p = params or ParametrosGrade()
    capital_por_nivel = p.capital_inicial / p.n_niveis

    niveis: List[NivelGrade] = []
    grade_ativa = False
    trades: List[Trade] = []
    capital = p.capital_inicial
    equity_curve = [capital]
    peak_equity = capital
    max_drawdown_pct = 0.0

    def _registrar_equity():
        nonlocal peak_equity, max_drawdown_pct
        equity_curve.append(capital)
        peak_equity = max(peak_equity, capital)
        if peak_equity > 0:
            max_drawdown_pct = max(max_drawdown_pct, (peak_equity - capital) / peak_equity * 100)

    def _fechar(lvl: NivelGrade, preco_saida_bruto: float, instante, motivo: str, lado_slippage: int):
        nonlocal capital
        preco_saida = preco_saida_bruto * (1 - lado_slippage * slippage_pct)
        quantidade = capital_por_nivel / lvl.preco_entrada_ajustado
        valor_entrada = quantidade * lvl.preco_entrada_ajustado
        valor_saida = quantidade * preco_saida
        fees = (valor_entrada + valor_saida) * fee_rate
        pnl = valor_saida - valor_entrada - fees
        pnl_pct = pnl / valor_entrada * 100 if valor_entrada else 0.0
        capital += pnl
        trades.append(Trade(
            entry_price=lvl.preco_entrada_ajustado, exit_price=preco_saida, quantity=quantidade,
            pnl=pnl, pnl_pct=pnl_pct, fees=fees,
            entry_time=lvl.instante_entrada, exit_time=instante, exit_reason=motivo,
        ))
        lvl.ocupado = False
        _registrar_equity()

    for idx, row in df.iterrows():
        regime = row["regime"]

        if grade_ativa and regime == "trending":
            for lvl in niveis:
                if lvl.ocupado:
                    _fechar(lvl, row["close"], idx, EXIT_REASON_REGIME, lado_slippage=1)
            grade_ativa = False
            niveis = []
            continue

        if grade_ativa:
            for lvl in niveis:
                if lvl.ocupado:
                    if row["high"] >= lvl.preco_venda:
                        _fechar(lvl, lvl.preco_venda, idx, EXIT_REASON_GRID, lado_slippage=1)
                elif row["low"] <= lvl.preco_compra:
                    preco_entrada = lvl.preco_compra * (1 + slippage_pct)
                    lvl.ocupado = True
                    lvl.preco_entrada_ajustado = preco_entrada
                    lvl.instante_entrada = idx
        elif regime == "sideways":
            niveis = _criar_niveis(row["bb_lower"], row["bb_upper"], p.n_niveis)
            grade_ativa = True

    wins = [t for t in trades if t.pnl > 0]
    total_return_pct = (capital - p.capital_inicial) / p.capital_inicial * 100 if p.capital_inicial else 0.0
    win_rate = len(wins) / len(trades) * 100 if trades else 0.0
    buy_hold_return_pct = _buy_hold_return_pct(df, p.capital_inicial, 0, fee_rate, slippage_pct)
    edge_return_pct = total_return_pct - buy_hold_return_pct

    metrics = _calculate_advanced_metrics(
        trades,
        total_return_pct=total_return_pct,
        buy_hold_return_pct=buy_hold_return_pct,
        max_drawdown_pct=max_drawdown_pct,
        period_start=df.index[0] if len(df) else None,
        period_end=df.index[-1] if len(df) else None,
    )

    return BacktestResult(
        trades=trades,
        initial_capital=p.capital_inicial,
        final_capital=capital,
        total_return_pct=total_return_pct,
        win_rate=win_rate,
        total_trades=len(trades),
        max_drawdown_pct=max_drawdown_pct,
        buy_hold_return_pct=buy_hold_return_pct,
        edge_return_pct=edge_return_pct,
        **metrics,
    )


def run_grid_scan(pares: Optional[List[str]] = None, params: Optional[ParametrosGrade] = None):
    """Roda `simular_grade` sobre cada par de `pares` (default
    `UNIVERSO_H11`, D7) e aplica `evaluate_approval` -- sem criterio de
    aprovacao novo (FR-006)."""
    from backtesting.approval import evaluate_approval
    from backtesting.horizonte import UNIVERSO_H11
    from config.settings import TIMEFRAME
    from data.fetcher import fetch_ohlcv
    from strategy.ema_rsi import EmaRsiStrategy

    pares = pares if pares is not None else UNIVERSO_H11
    estrategia = EmaRsiStrategy()
    saida = []
    for par in pares:
        try:
            df = fetch_ohlcv(par, TIMEFRAME, 2000)
            prep = estrategia.calculate_indicators(df)
            resultado = simular_grade(prep, params)
            if len(prep) and float(prep["close"].iloc[-1]) < MIN_PRICE_USDT:
                resultado.below_min_price = True
            veredito = evaluate_approval(resultado)
            saida.append((par, resultado, veredito))
        except Exception as exc:
            log.warning(f"{par}: falha na simulacao de grade: {exc}")
            saida.append((par, None, evaluate_approval(None)))
    return saida
