"""H34 -- reversao pos-liquidacao (padrao de vela: pavio + pico de volume),
spec 070. Primeira hipotese avaliada inteiramente pelo harness comum E1-E6
(`backtesting/bateria_hipotese.py::rodar_bateria`) em vez de reimplementar a
orquestracao -- ver `specs/070-h34-reversao-pos-liquidacao/research.md`
para o raciocinio completo por tras de cada decisao abaixo (D1-D4),
declaradas ANTES de qualquer medicao real:

D1: pavio inferior >= 50% do range do candle + fechamento de recuperacao
(`strategy/reversao_pos_liquidacao.py::LIMIAR_PAVIO_FRACAO_RANGE`).

D2: volume >= 3x a media movel de 20 candles
(`strategy/reversao_pos_liquidacao.py::LIMIAR_VOLUME_MULTIPLICADOR`).

D3: universo = UNIVERSO_H11 (12 pares, mesma familia direcional de H26).

D4: TIMEFRAME padrao do projeto, 2000 candles por par (~333 dias) --
mesma ordem de historico de H26/H14 pre-historico-estendido.

Sem dado de liquidacao real (Binance nao publica historico livre de
`forceOrder`): D1/D2 sao um PROXY sobre OHLCV, nao a cascata medida
diretamente -- risco declarado de reproduzir H3 (reversao a media via
Bollinger+RSI, ja reprovada) com um filtro diferente sobre o mesmo ruido.
"""
from typing import Dict, Optional

import pandas as pd

from backtesting.bateria_hipotese import RelatorioBateria, rodar_bateria
from backtesting.engine import BacktestResult, simulate_backtest
from backtesting.horizonte import UNIVERSO_H11
from config.settings import BACKTEST_FEE_RATE, BACKTEST_SLIPPAGE_PCT, TIMEFRAME
from data.fetcher import fetch_ohlcv
from strategy.reversao_pos_liquidacao import ReversaoPosLiquidacaoStrategy

N_CANDLES = 2000  # ~333 dias em 4h -- D4


def gerar_resultado(candles: pd.DataFrame, custo_zero: bool) -> BacktestResult:
    strategy = ReversaoPosLiquidacaoStrategy()
    df = strategy.calculate_indicators(candles)
    fee_rate = 0.0 if custo_zero else BACKTEST_FEE_RATE
    slippage_pct = 0.0 if custo_zero else BACKTEST_SLIPPAGE_PCT
    return simulate_backtest(df, strategy, fee_rate=fee_rate, slippage_pct=slippage_pct)


def _candles_sinteticas_sem_padrao(n: int = 400) -> pd.DataFrame:
    """Serie sintetica construida para NUNCA bater D1/D2: sem pavio (open ==
    low) e volume constante (nunca 3x a propria media) -- usada por
    `teste_sanidade` (E1) para isolar defeito de motor de resultado de
    estrategia real."""
    idx = pd.date_range("2026-01-01", periods=n, freq="4h")
    preco = 100.0 + pd.Series(range(n), dtype=float) * 0.01
    return pd.DataFrame({
        "open": preco, "high": preco * 1.001, "low": preco, "close": preco * 1.0005,
        "volume": 1000.0,
    }, index=idx)


def teste_sanidade() -> bool:
    """E1: zero trades sobre serie sem pavio nem pico de volume."""
    resultado = gerar_resultado(_candles_sinteticas_sem_padrao(), False)
    return resultado.total_trades == 0


def avaliar_par(par: str, timeframe: str = TIMEFRAME, n_candles: int = N_CANDLES) -> Optional[RelatorioBateria]:
    """`None` quando o par nao tem historico suficiente para buscar."""
    candles = fetch_ohlcv(par, timeframe, limit=n_candles)
    if candles is None or len(candles) == 0:
        return None
    return rodar_bateria(candles, gerar_resultado, teste_sanidade=teste_sanidade)


def avaliar_universo(pares: Optional[list] = None) -> Dict[str, RelatorioBateria]:
    pares = list(pares) if pares is not None else list(UNIVERSO_H11)
    resultados = {}
    for par in pares:
        r = avaliar_par(par)
        if r is not None:
            resultados[par] = r
    return resultados
