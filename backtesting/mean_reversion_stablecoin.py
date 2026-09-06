"""H37 -- mean reversion em par de stablecoin (USDC/USDT), spec 072.
Segunda hipotese a rodar pelo harness comum E1-E6
(`backtesting/bateria_hipotese.py::rodar_bateria`), depois de H34.

`strategy/mean_reversion.py::MeanReversionStrategy` (H3, ja testada e
reprovada em BTC/SOL/ETH -- secao 4.4 do registro) roda SEM NENHUMA
alteracao de codigo sobre USDC/USDT, unico par avaliado (a hipotese e
sobre o mecanismo de reversao deste instrumento especifico -- resgate 1:1
garantido pelo emissor -- nao uma familia de pares, diferente de H34/H35).

Obstaculo declarado antes de medir (ver
specs/072-h37-mean-reversion-stablecoin/research.md D3): a literatura
descreve a janela de arbitragem de stablecoin como durando SEGUNDOS,
dominada por bots MEV -- um candle de 4h pode nao ter resolucao para
capturar essa reversao. Expectativa honesta: resultado indistinguivel de
ruido em torno de um preco estruturalmente estavel, nao necessariamente
um sinal capturavel e ruim como o H3 original.
"""
from typing import Optional

import pandas as pd

from backtesting.bateria_hipotese import RelatorioBateria, rodar_bateria
from backtesting.engine import BacktestResult, simulate_backtest
from config.settings import BACKTEST_FEE_RATE, BACKTEST_SLIPPAGE_PCT, TIMEFRAME
from data.fetcher import fetch_ohlcv
from strategy.mean_reversion import MeanReversionStrategy

PAR = "USDC/USDT"
N_CANDLES = 2000  # ~11 meses, confirmado disponivel por probe real nesta sessao


def gerar_resultado(candles: pd.DataFrame, custo_zero: bool) -> BacktestResult:
    strategy = MeanReversionStrategy()
    df = strategy.calculate_indicators(candles)
    fee_rate = 0.0 if custo_zero else BACKTEST_FEE_RATE
    slippage_pct = 0.0 if custo_zero else BACKTEST_SLIPPAGE_PCT
    return simulate_backtest(df, strategy, fee_rate=fee_rate, slippage_pct=slippage_pct)


def _candles_preco_constante(n: int = 400) -> pd.DataFrame:
    """Serie sintetica sem volatilidade -- Bollinger Bands colapsam para um
    preco unico, a banda inferior nunca fica abaixo do proprio preco, entao
    o sinal de compra (preco <= banda inferior) nunca dispara. Usada por
    `teste_sanidade` (E1) para isolar defeito de motor de resultado real."""
    idx = pd.date_range("2026-01-01", periods=n, freq="4h")
    preco = 1.0
    return pd.DataFrame({
        "open": preco, "high": preco, "low": preco, "close": preco, "volume": 1_000_000.0,
    }, index=idx)


def teste_sanidade() -> bool:
    """E1: zero trades sobre serie de preco constante (sem volatilidade)."""
    resultado = gerar_resultado(_candles_preco_constante(), False)
    return resultado.total_trades == 0


def avaliar() -> Optional[RelatorioBateria]:
    """Unico par avaliado (D1) -- sem loop de universo, diferente de H34/H35.
    `None` quando a busca de candles nao devolve historico (mesma politica
    de "nunca aprovado por omissao de dado" de `reversao_pos_liquidacao.py::avaliar_par`)."""
    candles = fetch_ohlcv(PAR, TIMEFRAME, N_CANDLES)
    if candles is None or len(candles) == 0:
        return None
    return rodar_bateria(candles, gerar_resultado, teste_sanidade=teste_sanidade)
