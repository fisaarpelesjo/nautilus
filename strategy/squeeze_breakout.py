import pandas as pd
import ta
from strategy.base import BaseStrategy, Signal, TradeSignal
from utils.logger import get_logger

log = get_logger("squeeze_breakout")


class SqueezeBreakoutStrategy(BaseStrategy):
    """
    Compressao de volatilidade (Bollinger Band squeeze) seguida de rompimento
    com volume: banda estreita relativa ao proprio historico recente do par
    (nao um limiar fixo, que nao generalizaria entre pares de volatilidade
    muito diferente) sinaliza acumulacao antes de um movimento direcional;
    compra no rompimento da banda superior confirmado por volume acima da
    media, apostando que baixa volatilidade antecede expansao sustentada
    -- mecanismo oposto ao mean-reversion (que aposta em reversao, nao
    continuacao, do movimento esticado).

    Sai quando o preco volta a cruzar a media (fim do movimento de expansao).
    """

    def __init__(self, bb_period: int = 20, bb_std: float = 2.0,
                 squeeze_lookback: int = 120, squeeze_percentile: float = 0.2,
                 volume_ma_period: int = 20, volume_min_ratio: float = 1.2):
        self.bb_period = bb_period
        self.bb_std = bb_std
        self.squeeze_lookback = squeeze_lookback
        self.squeeze_percentile = squeeze_percentile
        self.volume_ma_period = volume_ma_period
        self.volume_min_ratio = volume_min_ratio

    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        bb = ta.volatility.BollingerBands(df["close"], window=self.bb_period, window_dev=self.bb_std)
        df["bb_upper"] = bb.bollinger_hband()
        df["bb_middle"] = bb.bollinger_mavg()
        df["bb_lower"] = bb.bollinger_lband()
        df["bb_bandwidth"] = (df["bb_upper"] - df["bb_lower"]) / df["bb_middle"]
        df["squeeze_threshold"] = df["bb_bandwidth"].rolling(self.squeeze_lookback).quantile(self.squeeze_percentile)
        df["was_squeezed"] = df["bb_bandwidth"].shift(1) <= df["squeeze_threshold"].shift(1)
        df["volume_ma"] = df["volume"].rolling(self.volume_ma_period).mean()
        df.dropna(inplace=True)
        return df

    def generate_signal(self, df: pd.DataFrame) -> TradeSignal:
        min_rows = self.squeeze_lookback + self.bb_period + 1
        if len(df) < min_rows:
            return TradeSignal(Signal.HOLD, df.iloc[-1]["close"] if len(df) else 0, "Dados insuficientes")

        df = self.calculate_indicators(df)
        if len(df) < 1:
            return TradeSignal(Signal.HOLD, df.iloc[-1]["close"] if len(df) else 0, "Dados insuficientes")

        curr = df.iloc[-1]
        price = curr["close"]
        volume_ok = curr["volume"] >= curr["volume_ma"] * self.volume_min_ratio
        breakout_up = price > curr["bb_upper"]

        if curr["was_squeezed"] and breakout_up and volume_ok:
            log.info(f"COMPRA | rompimento pos-squeeze (bandwidth={curr['bb_bandwidth']:.4f}) | volume confirmado")
            return TradeSignal(Signal.BUY, price, f"Squeeze + rompimento: bandwidth={curr['bb_bandwidth']:.4f}, volume >= {self.volume_min_ratio}x media")

        if price < curr["bb_middle"]:
            log.info(f"VENDA | preco voltou abaixo da media (movimento de expansao encerrado)")
            return TradeSignal(Signal.SELL, price, "Preco cruzou de volta abaixo da BB media -- fim do movimento")

        return TradeSignal(Signal.HOLD, price, f"Aguardando squeeze+rompimento (bandwidth={curr['bb_bandwidth']:.4f}, limiar={curr['squeeze_threshold']:.4f})")
