"""H39 -- arbitragem estatistica via PCA/eigenportfolio (Avellaneda-Lee,
2008), spec 075. Decompoe o universo inteiro
(UNIVERSO_AMPLO_HISTORICO_COMPLETO, 22 pares, ja usado por H10/H29) em
componentes principais dos retornos, regride cada ativo contra os
fatores comuns, integra o residuo e modela o processo integrado como
Ornstein-Uhlenbeck. Relacao MUITAS-para-muitas -- diferente de H10
(cointegracao par-a-par) e H29 (copula par-a-par). Ver
specs/075-h39-pca-eigenportfolio/research.md para D1-D6 declarados ANTES
de qualquer medicao:

D1: universo = UNIVERSO_AMPLO_HISTORICO_COMPLETO, indice alinhado pela
intersecao comum (mesma correcao de M14, spec 052).

D2: componentes = suficientes para explicar >=55% da variancia dos
retornos padronizados de TREINO, teto de 10.

D3: pesos de fator e parametros OU estimados SO no treino
(split_train_validation, mesmo corte de qualquer outra hipotese desta
bateria), aplicados sem reajuste na validacao.

D4: meia-vida do residuo integrado (treino) filtrada pela mesma faixa ja
usada por H10 ([2, 120], PairsParams.meia_vida_min/max) -- reusa
pairs_trading.py::meia_vida_reversao, nao reimplementa o estimador.

D5: entrada s<=-1.25, saida s>=-0.5 -- limiares classicos do paper,
fixados antes de medir.

D6: SEM HEDGE dos fatores -- o bot e long-only (CLAUDE.md). Esta
implementacao e uma aposta DIRECIONAL no ativo quando o residuo esta
esticado para baixo, nao uma posicao dollar-neutral como o metodo
original. Risco de fator (tipicamente BTC) permanece -- limitacao
declarada, nao escondida no resultado.
"""
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import ta

from backtesting.bateria_hipotese import RelatorioBateria, rodar_bateria
from backtesting.engine import BacktestResult, simulate_backtest
from backtesting.pairs_trading import UNIVERSO_AMPLO_HISTORICO_COMPLETO, meia_vida_reversao
from backtesting.validation import DEFAULT_VALIDATION_RATIO, split_train_validation
from config.settings import BACKTEST_FEE_RATE, BACKTEST_SLIPPAGE_PCT, TIMEFRAME
from data.fetcher import fetch_ohlcv
from strategy.base import BaseStrategy, Signal, TradeSignal

N_CANDLES = 6000
VARIANCIA_ALVO = 0.55   # D2
MAX_COMPONENTES = 10    # D2
MEIA_VIDA_MIN = 2       # D4
MEIA_VIDA_MAX = 120     # D4
S_SCORE_ENTRADA = -1.25  # D5
S_SCORE_SAIDA = -0.5     # D5


def _indice_comum(series: Dict[str, pd.Series]) -> pd.DatetimeIndex:
    indice = None
    for s in series.values():
        indice = s.index if indice is None else indice.intersection(s.index)
    return indice.sort_values()


def _componentes_pca(retornos_padronizados: pd.DataFrame) -> Tuple[np.ndarray, float]:
    """Autovetores (colunas) dos k primeiros componentes principais, e a
    fracao de variancia acumulada que eles explicam (D2)."""
    cov = np.cov(retornos_padronizados.to_numpy(), rowvar=False)
    autovalores, autovetores = np.linalg.eigh(cov)
    ordem = np.argsort(autovalores)[::-1]
    autovalores = autovalores[ordem]
    autovetores = autovetores[:, ordem]

    variancia_acumulada = np.cumsum(autovalores) / autovalores.sum()
    k = int(np.searchsorted(variancia_acumulada, VARIANCIA_ALVO) + 1)
    k = min(k, MAX_COMPONENTES, len(autovalores))
    return autovetores[:, :k], float(variancia_acumulada[k - 1])


def _ajustar_ou(x_treino: np.ndarray) -> Optional[Tuple[float, float]]:
    """AR(1) sobre o residuo integrado: X_t = a + b*X_{t-1} + erro.
    `None` quando b nao esta em (0,1) -- processo nao estacionario/
    revertente, sem media de equilibrio bem definida (D3)."""
    if len(x_treino) < 3:
        return None
    x_lag = x_treino[:-1]
    x_atual = x_treino[1:]
    matriz = np.column_stack([np.ones_like(x_lag), x_lag])
    coef, *_ = np.linalg.lstsq(matriz, x_atual, rcond=None)
    a, b = coef
    if not (0 < b < 1):
        return None
    residuos = x_atual - (a + b * x_lag)
    sigma_eq = float(np.std(residuos) * np.sqrt(1 / (1 - b ** 2)))
    if sigma_eq <= 0:
        return None
    media = float(a / (1 - b))
    return media, sigma_eq


class ResiduoStrategy(BaseStrategy):
    """BUY quando o s-score pre-calculado (parametros travados no treino)
    cruza <=S_SCORE_ENTRADA, SELL quando cruza >=S_SCORE_SAIDA. Sem SL/TP
    artificial alem do ATR ja generico do motor -- mesmo padrao de H36."""

    def __init__(self, s_score: pd.Series):
        self.s_score = s_score

    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        df["atr"] = ta.volatility.AverageTrueRange(
            df["high"], df["low"], df["close"], window=14
        ).average_true_range()
        s = self.s_score.reindex(df.index)
        prev = s.shift(1)
        df["cruza_entrada"] = (prev > S_SCORE_ENTRADA) & (s <= S_SCORE_ENTRADA)
        df["cruza_saida"] = (prev < S_SCORE_SAIDA) & (s >= S_SCORE_SAIDA)
        return df

    def generate_signal(self, df: pd.DataFrame) -> TradeSignal:
        if len(df) < 15:
            return TradeSignal(Signal.HOLD, df.iloc[-1]["close"] if len(df) else 0, "Dados insuficientes")
        df = self.calculate_indicators(df)
        curr = df.iloc[-1]
        price = curr["close"]
        if bool(curr["cruza_entrada"]):
            return TradeSignal(Signal.BUY, price, "PCA/OU: s-score cruzou limiar de entrada")
        if bool(curr["cruza_saida"]):
            return TradeSignal(Signal.SELL, price, "PCA/OU: s-score cruzou limiar de saida")
        return TradeSignal(Signal.HOLD, price, "Sem cruzamento de s-score")


def precompute_signals(candles: pd.DataFrame, s_score: pd.Series) -> pd.Series:
    """Sinal vetorizado sobre o indice inteiro -- mesma correcao de
    performance ja aplicada em H36: evita recalcular por candle dentro do
    loop de simulate_backtest."""
    s = s_score.reindex(candles.index)
    prev = s.shift(1)
    entra = (prev > S_SCORE_ENTRADA) & (s <= S_SCORE_ENTRADA)
    sai = (prev < S_SCORE_SAIDA) & (s >= S_SCORE_SAIDA)
    sinal = pd.Series(Signal.HOLD, index=candles.index)
    sinal[sai] = Signal.SELL
    sinal[entra] = Signal.BUY
    return sinal


def gerar_resultado_par(candles: pd.DataFrame, custo_zero: bool, s_score: pd.Series) -> BacktestResult:
    strategy = ResiduoStrategy(s_score)
    df = strategy.calculate_indicators(candles)
    sinais = precompute_signals(candles, s_score)
    fee_rate = 0.0 if custo_zero else BACKTEST_FEE_RATE
    slippage_pct = 0.0 if custo_zero else BACKTEST_SLIPPAGE_PCT
    return simulate_backtest(df, strategy, fee_rate=fee_rate, slippage_pct=slippage_pct, precomputed_signals=sinais)


def _candles_s_score_constante(n: int = 200) -> pd.DataFrame:
    idx = pd.date_range("2026-01-01", periods=n, freq="4h")
    return pd.DataFrame({
        "open": 100.0, "high": 101.0, "low": 99.0, "close": 100.0, "volume": 1000.0,
    }, index=idx)


def teste_sanidade() -> bool:
    """E1: zero trades quando o s-score nunca cruza limiar (serie
    constante em zero -- nunca <=-1.25 nem >=-0.5 partindo de zero, o
    cruzamento exige vir de cima/baixo do limiar)."""
    candles = _candles_s_score_constante()
    s_score = pd.Series(0.0, index=candles.index)
    resultado = gerar_resultado_par(candles, False, s_score)
    return resultado.total_trades == 0


@dataclass
class ResultadoAtivoPCA:
    par: str
    n_componentes: int
    variancia_explicada: float
    meia_vida_residuo: float
    excluido: bool
    motivo_exclusao: Optional[str] = None
    relatorio: Optional[RelatorioBateria] = None


def avaliar_universo(pares: Optional[List[str]] = None) -> List[ResultadoAtivoPCA]:
    pares = list(pares) if pares is not None else list(UNIVERSO_AMPLO_HISTORICO_COMPLETO)

    precos_por_par: Dict[str, pd.DataFrame] = {}
    for par in pares:
        df = fetch_ohlcv(par, TIMEFRAME, N_CANDLES)
        if df is not None and len(df):
            precos_por_par[par] = df

    if len(precos_por_par) < 3:
        return []

    indice = _indice_comum({p: df["close"] for p, df in precos_por_par.items()})
    fechamentos = pd.DataFrame({p: df["close"].reindex(indice) for p, df in precos_por_par.items()}).dropna()
    retornos = fechamentos.pct_change().dropna()

    treino_ret, _ = split_train_validation(retornos, validation_ratio=DEFAULT_VALIDATION_RATIO)
    n_treino = len(treino_ret)

    # Par com preco parado (variancia zero) na fatia de treino contaminaria
    # a decomposicao COMPARTILHADA (std=0 -> padronizado=inf/nan -> cov/eigh
    # corrompidos para o universo inteiro, nao so o par ofensor) -- excluido
    # antes do PCA, nunca silenciosamente propagado (achado de code-review).
    desvio_treino_bruto = treino_ret.std()
    pares_sem_variancia = desvio_treino_bruto[desvio_treino_bruto == 0].index.tolist()
    if pares_sem_variancia:
        fechamentos = fechamentos.drop(columns=pares_sem_variancia)
        retornos = retornos.drop(columns=pares_sem_variancia)
        treino_ret = treino_ret.drop(columns=pares_sem_variancia)
    if len(fechamentos.columns) < 3:
        return [
            ResultadoAtivoPCA(par=p, n_componentes=0, variancia_explicada=0.0,
                              meia_vida_residuo=float("nan"), excluido=True,
                              motivo_exclusao="preco sem variancia no treino")
            for p in pares_sem_variancia
        ]

    media_treino = treino_ret.mean()
    desvio_treino = treino_ret.std()
    padronizado_treino = (treino_ret - media_treino) / desvio_treino
    padronizado_completo = (retornos - media_treino) / desvio_treino

    autovetores, variancia_explicada = _componentes_pca(padronizado_treino)
    n_componentes = autovetores.shape[1]

    fatores_treino = padronizado_treino.to_numpy() @ autovetores
    fatores_completo = padronizado_completo.to_numpy() @ autovetores

    resultados: List[ResultadoAtivoPCA] = []
    for par in fechamentos.columns:
        y_treino = treino_ret[par].to_numpy()
        matriz_treino = np.column_stack([np.ones(len(y_treino)), fatores_treino])
        beta, *_ = np.linalg.lstsq(matriz_treino, y_treino, rcond=None)

        matriz_completa = np.column_stack([np.ones(len(retornos)), fatores_completo])
        previsto = matriz_completa @ beta
        residuo = retornos[par].to_numpy() - previsto
        x_integrado = np.cumsum(residuo)

        meia_vida = meia_vida_reversao(x_integrado[:n_treino])
        fora_da_faixa = not (MEIA_VIDA_MIN <= meia_vida <= MEIA_VIDA_MAX)

        if fora_da_faixa:
            resultados.append(ResultadoAtivoPCA(
                par=par, n_componentes=n_componentes, variancia_explicada=variancia_explicada,
                meia_vida_residuo=meia_vida, excluido=True,
                motivo_exclusao=f"meia-vida fora de [{MEIA_VIDA_MIN},{MEIA_VIDA_MAX}]",
            ))
            continue

        ou = _ajustar_ou(x_integrado[:n_treino])
        if ou is None:
            resultados.append(ResultadoAtivoPCA(
                par=par, n_componentes=n_componentes, variancia_explicada=variancia_explicada,
                meia_vida_residuo=meia_vida, excluido=True,
                motivo_exclusao="processo OU nao estacionario (fit AR(1) falhou)",
            ))
            continue

        media, sigma_eq = ou
        s_score = pd.Series((x_integrado - media) / sigma_eq, index=retornos.index)

        candles_par = precos_por_par[par].reindex(indice).dropna()
        candles_par = candles_par.loc[candles_par.index.intersection(s_score.index)]
        s_score = s_score.reindex(candles_par.index)

        def _gerar(fatia: pd.DataFrame, custo_zero: bool, _s: pd.Series = s_score) -> BacktestResult:
            return gerar_resultado_par(fatia, custo_zero, _s)

        relatorio = rodar_bateria(candles_par, _gerar, teste_sanidade=teste_sanidade)
        resultados.append(ResultadoAtivoPCA(
            par=par, n_componentes=n_componentes, variancia_explicada=variancia_explicada,
            meia_vida_residuo=meia_vida, excluido=False, relatorio=relatorio,
        ))

    return resultados
