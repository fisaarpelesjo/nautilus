import pandas as pd
import ta
from config.settings import EMA_FAST, EMA_SLOW, EMA_TREND, RSI_PERIOD, RSI_OVERSOLD, RSI_OVERBOUGHT
from strategy.base import BaseStrategy, TradeSignal, Signal
from utils.logger import get_logger

log = get_logger("ema_rsi")

class EmaRsiStrategy(BaseStrategy):
    """
    Sinal de COMPRA:  EMA21 cruza acima EMA50  +  preço > EMA200  +  RSI < 65
    Sinal de VENDA:   EMA21 cruza abaixo EMA50  +  RSI > 35
    """

    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        df["ema_fast"]  = ta.trend.EMAIndicator(df["close"], window=EMA_FAST).ema_indicator()
        df["ema_slow"]  = ta.trend.EMAIndicator(df["close"], window=EMA_SLOW).ema_indicator()
        df["ema_trend"] = ta.trend.EMAIndicator(df["close"], window=EMA_TREND).ema_indicator()
        df["rsi"]       = ta.momentum.RSIIndicator(df["close"], window=RSI_PERIOD).rsi()
        df["macd"]      = ta.trend.MACD(df["close"]).macd_diff()
        df["atr"]       = ta.volatility.AverageTrueRange(df["high"], df["low"], df["close"], window=14).average_true_range()
        df.dropna(inplace=True)
        return df

    def generate_signal(self, df: pd.DataFrame) -> TradeSignal:
        df = self.calculate_indicators(df)

        if len(df) < 2:
            return TradeSignal(Signal.HOLD, df.iloc[-1]["close"] if len(df) else 0, "Dados insuficientes")

        prev  = df.iloc[-2]
        curr  = df.iloc[-1]
        price = curr["close"]
        rsi   = curr["rsi"]

        bullish_cross = prev["ema_fast"] < prev["ema_slow"] and curr["ema_fast"] > curr["ema_slow"]
        bearish_cross = prev["ema_fast"] > prev["ema_slow"] and curr["ema_fast"] < curr["ema_slow"]

        above_trend = price > curr["ema_trend"]

        if bullish_cross and above_trend and rsi < RSI_OVERBOUGHT:
            log.info(f"COMPRA | EMA cross alta + acima EMA{EMA_TREND} | RSI={rsi:.1f} | Preco={price:.2f}")
            return TradeSignal(Signal.BUY, price, f"EMA{EMA_FAST} cruzou acima EMA{EMA_SLOW} | acima EMA{EMA_TREND} | RSI={rsi:.1f}")

        if bearish_cross and rsi > RSI_OVERSOLD:
            log.info(f"VENDA | EMA cross baixa | RSI={rsi:.1f} | Preco={price:.2f}")
            return TradeSignal(Signal.SELL, price, f"EMA{EMA_FAST} cruzou abaixo EMA{EMA_SLOW} | RSI={rsi:.1f}")

        return TradeSignal(Signal.HOLD, price, f"Aguardando | EMA_fast={curr['ema_fast']:.2f} EMA_slow={curr['ema_slow']:.2f} RSI={rsi:.1f}")
