from dataclasses import dataclass
import pandas as pd
import ta
from config.settings import (
    EMA_FAST,
    EMA_SLOW,
    EMA_TREND,
    RSI_PERIOD,
    RSI_OVERSOLD,
    RSI_OVERBOUGHT,
    VOLUME_MA_PERIOD,
    VOLUME_MIN_RATIO,
    BB_PERIOD,
    BB_STD,
    PULLBACK_ENTRY_ENABLED,
    PULLBACK_RSI_MIN,
    PULLBACK_MAX_DISTANCE_PCT,
)
from strategy.base import BaseStrategy, TradeSignal, Signal
from utils.logger import get_logger

log = get_logger("ema_rsi")


@dataclass(frozen=True)
class EmaRsiParams:
    ema_fast: int = EMA_FAST
    ema_slow: int = EMA_SLOW
    ema_trend: int = EMA_TREND
    rsi_period: int = RSI_PERIOD
    rsi_oversold: int = RSI_OVERSOLD
    rsi_overbought: int = RSI_OVERBOUGHT
    volume_ma_period: int = VOLUME_MA_PERIOD
    volume_min_ratio: float = VOLUME_MIN_RATIO
    bb_period: int = BB_PERIOD
    bb_std: float = BB_STD
    pullback_entry_enabled: bool = PULLBACK_ENTRY_ENABLED
    pullback_rsi_min: int = PULLBACK_RSI_MIN
    pullback_max_distance_pct: float = PULLBACK_MAX_DISTANCE_PCT


class EmaRsiStrategy(BaseStrategy):
    """
    Sinal de COMPRA: cruzamento EMA rapido/lento ou pullback em tendencia.
    Sinal de VENDA: EMA rapido cruza abaixo EMA lento + RSI acima do piso.
    """

    def __init__(self, params: EmaRsiParams | None = None):
        self.params = params or EmaRsiParams()

    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        p = self.params
        df = df.copy()
        df["ema_fast"]  = ta.trend.EMAIndicator(df["close"], window=p.ema_fast).ema_indicator()
        df["ema_slow"]  = ta.trend.EMAIndicator(df["close"], window=p.ema_slow).ema_indicator()
        df["ema_trend"] = ta.trend.EMAIndicator(df["close"], window=p.ema_trend).ema_indicator()
        df["rsi"]       = ta.momentum.RSIIndicator(df["close"], window=p.rsi_period).rsi()
        df["macd"]      = ta.trend.MACD(df["close"]).macd_diff()
        df["atr"]       = ta.volatility.AverageTrueRange(df["high"], df["low"], df["close"], window=14).average_true_range()
        df["volume_ma"] = df["volume"].rolling(window=p.volume_ma_period).mean()
        bb = ta.volatility.BollingerBands(df["close"], window=p.bb_period, window_dev=p.bb_std)
        df["bb_upper"]  = bb.bollinger_hband()
        df["bb_middle"] = bb.bollinger_mavg()
        df["bb_lower"]  = bb.bollinger_lband()
        df.dropna(inplace=True)
        return df

    def generate_signal(self, df: pd.DataFrame) -> TradeSignal:
        p = self.params
        df = self.calculate_indicators(df)

        if len(df) < 2:
            return TradeSignal(Signal.HOLD, df.iloc[-1]["close"] if len(df) else 0, "Dados insuficientes")

        prev  = df.iloc[-2]
        curr  = df.iloc[-1]
        price = curr["close"]
        rsi   = curr["rsi"]

        bullish_cross = prev["ema_fast"] < prev["ema_slow"] and curr["ema_fast"] > curr["ema_slow"]
        bearish_cross = prev["ema_fast"] > prev["ema_slow"] and curr["ema_fast"] < curr["ema_slow"]

        above_trend    = price > curr["ema_trend"]
        volume_ok      = curr["volume"] >= curr["volume_ma"] * p.volume_min_ratio
        not_overextended = price <= curr["bb_upper"]
        pullback_entry = self._is_pullback_entry(curr)

        if bullish_cross and above_trend and rsi < p.rsi_overbought and volume_ok and not_overextended:
            log.info(f"COMPRA | EMA cross alta + acima EMA{p.ema_trend} | RSI={rsi:.1f} | Vol={curr['volume']:.0f} (MA={curr['volume_ma']:.0f}) | BB_upper={curr['bb_upper']:.4f}")
            return TradeSignal(Signal.BUY, price, f"EMA{p.ema_fast} cruzou acima EMA{p.ema_slow} | acima EMA{p.ema_trend} | RSI={rsi:.1f} | vol OK | BB OK")

        if pullback_entry and volume_ok and not_overextended:
            log.info(f"COMPRA | pullback em tendencia | RSI={rsi:.1f} | Vol={curr['volume']:.0f} (MA={curr['volume_ma']:.0f}) | low={curr['low']:.4f}")
            return TradeSignal(Signal.BUY, price, f"Pullback em tendencia EMA{p.ema_fast}/{p.ema_slow}/{p.ema_trend} | RSI={rsi:.1f} | vol OK | BB OK")

        if bearish_cross and rsi > p.rsi_oversold:
            log.info(f"VENDA | EMA cross baixa | RSI={rsi:.1f}")
            return TradeSignal(Signal.SELL, price, f"EMA{p.ema_fast} cruzou abaixo EMA{p.ema_slow} | RSI={rsi:.1f}")

        return TradeSignal(Signal.HOLD, price, f"Aguardando | EMA_fast={curr['ema_fast']:.2f} EMA_slow={curr['ema_slow']:.2f} RSI={rsi:.1f}")

    def _is_pullback_entry(self, curr: pd.Series) -> bool:
        p = self.params
        if not p.pullback_entry_enabled:
            return False

        price = curr["close"]
        rsi = curr["rsi"]
        trend_aligned = curr["ema_fast"] > curr["ema_slow"] > curr["ema_trend"] and price > curr["ema_trend"]
        rsi_ok = p.pullback_rsi_min <= rsi < p.rsi_overbought
        low = curr.get("low", price)
        near_slow_ema = low <= curr["ema_slow"] * (1 + p.pullback_max_distance_pct)
        recovered_fast_ema = price > curr["ema_fast"]
        bullish_close = price > curr.get("open", price)

        return trend_aligned and rsi_ok and near_slow_ema and recovered_fast_ema and bullish_close
