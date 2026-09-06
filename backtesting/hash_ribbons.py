"""H36 -- hash ribbons: capitulacao de mineradores (spec 073). Quarta
hipotese avaliada pelo harness comum E1-E6
(`backtesting/bateria_hipotese.py::rodar_bateria`). Ver
`specs/073-h36-hash-ribbons/research.md` para D1-D5 declarados ANTES de
qualquer medicao real:

D1: cruzamento de medias moveis simples de 30/60 dias do hashrate, sem
suavizacao adicional (`strategy/hash_ribbons.py::HashRibbonsStrategy`).

D2: entrada/saida pelo proprio indicador, SL/TP/trailing por ATR do motor
permanece ativo sem alteracao (mesmo comportamento que a producao teria).

D3: candles anteriores ao inicio real do historico de hashrate disponivel
sao DESCARTADOS, nunca cruzamento presumido antes de existir dado real.

D4: unico par avaliado (BTC/USDT) -- hashrate e exclusivo da rede
Bitcoin, sem universo multi-par.

D5: amostra esperada pequena por construcao (no maximo ~16 cruzamentos de
alta na serie completa, medido por probe real) -- mesma categoria de
risco de H34/H10 pre-spec-054.

Compara-se, no registro final, com H17/H32 (mesma fonte de dado,
mecanismo de sinal categoricamente diferente: atributo de classificador
vs. sinal de entrada/saida direto).
"""
from typing import Optional

import pandas as pd

from backtesting.bateria_hipotese import RelatorioBateria, rodar_bateria
from backtesting.engine import BacktestResult, simulate_backtest
from config.settings import BACKTEST_FEE_RATE, BACKTEST_SLIPPAGE_PCT, TIMEFRAME
from data.fetcher import fetch_ohlcv
from data.onchain import fetch_onchain_series
from strategy.hash_ribbons import HashRibbonsStrategy, precompute_signals

PAR = "BTC/USDT"
N_CANDLES = 7000  # cobre com margem a janela real de hashrate disponivel (D4), confirmado por probe real


def gerar_resultado(candles: pd.DataFrame, custo_zero: bool, hashrate_diario: pd.Series) -> BacktestResult:
    strategy = HashRibbonsStrategy(hashrate_diario)
    df = strategy.calculate_indicators(candles)
    # precomputed_signals evita que simulate_backtest chame generate_signal()
    # por candle (cada chamada recalcularia o alinhamento causal sobre uma
    # fatia crescente -- O(n^2), achado de code-review). O sinal e causal e
    # nao depende de quantos candles totais existem, entao calcular uma vez
    # sobre o indice inteiro e correto, nao uma aproximacao.
    sinais = precompute_signals(candles, hashrate_diario)
    fee_rate = 0.0 if custo_zero else BACKTEST_FEE_RATE
    slippage_pct = 0.0 if custo_zero else BACKTEST_SLIPPAGE_PCT
    return simulate_backtest(df, strategy, fee_rate=fee_rate, slippage_pct=slippage_pct, precomputed_signals=sinais)


def _hashrate_sem_cruzamento(n: int = 200) -> pd.Series:
    """Serie monotonicamente crescente -- media de 30d sempre acima da de
    60d, nunca cruza. Usada por `teste_sanidade` (E1) para isolar defeito
    de motor de resultado de estrategia real. Indice tz-aware (UTC), mesmo
    formato real de `data.onchain.fetch_onchain_series`."""
    idx = pd.date_range("2026-01-01", periods=n, freq="D", tz="UTC")
    return pd.Series(range(1, n + 1), index=idx, dtype=float)


def teste_sanidade() -> bool:
    """E1: zero trades quando o hashrate nunca cruza (serie monotonica)."""
    hashrate = _hashrate_sem_cruzamento()
    idx_candles = pd.date_range("2026-01-05", periods=400, freq="4h")
    candles = pd.DataFrame({
        "open": 100.0, "high": 101.0, "low": 99.0, "close": 100.0, "volume": 1000.0,
    }, index=idx_candles)
    resultado = gerar_resultado(candles, False, hashrate)
    return resultado.total_trades == 0


def avaliar() -> Optional[RelatorioBateria]:
    """Unico par avaliado (D4). `None` quando faltar candles ou hashrate."""
    hashrate_df = fetch_onchain_series("hash-rate", timespan="3years")
    if len(hashrate_df) == 0:
        return None
    hashrate_diario = hashrate_df["value"]

    candles = fetch_ohlcv(PAR, TIMEFRAME, N_CANDLES)
    if candles is None or len(candles) == 0:
        return None

    # D3: descarta candles anteriores ao inicio real do hashrate -- nunca
    # cruzamento presumido antes de existir dado real.
    inicio_real = hashrate_diario.index.min()
    candles_tz = candles.index.tz_convert("UTC") if candles.index.tz else candles.index.tz_localize("UTC")
    candles = candles[candles_tz >= inicio_real]
    if len(candles) == 0:
        return None

    def _gerar(fatia: pd.DataFrame, custo_zero: bool) -> BacktestResult:
        return gerar_resultado(fatia, custo_zero, hashrate_diario)

    return rodar_bateria(candles, _gerar, teste_sanidade=teste_sanidade)
