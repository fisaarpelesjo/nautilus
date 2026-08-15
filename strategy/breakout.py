import pandas as pd
import ta
from config.settings import BREAKOUT_WINDOW
from strategy.base import BaseStrategy, Signal, TradeSignal
from utils.logger import get_logger

log = get_logger("breakout")


class BreakoutStrategy(BaseStrategy):
    """
    Rompimento de faixa (Donchian channel): compra quando o preco rompe a
    maxima das ultimas `window` velas, vende quando rompe a minima.
    """

    def __init__(self, window: int = BREAKOUT_WINDOW):
        self.window = window

    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        # shift(1) exclui o candle atual da propria janela -- sem isso, o
        # rompimento se compararia contra uma faixa que ja inclui o preco
        # que estamos avaliando (look-ahead).
        df["breakout_high"] = df["high"].rolling(window=self.window).max().shift(1)
        df["breakout_low"]  = df["low"].rolling(window=self.window).min().shift(1)
        df["atr"] = ta.volatility.AverageTrueRange(df["high"], df["low"], df["close"], window=14).average_true_range()
        df.dropna(inplace=True)
        return df

    def generate_signal(self, df: pd.DataFrame) -> TradeSignal:
        # Checado ANTES de calculate_indicators: ta.volatility.AverageTrueRange
        # (janela 14) levanta IndexError com menos de 14 linhas, nao produz
        # NaN graciosamente como os outros indicadores desta base de codigo.
        if len(df) < max(self.window, 14):
            return TradeSignal(Signal.HOLD, df.iloc[-1]["close"] if len(df) else 0, "Dados insuficientes")

        df = self.calculate_indicators(df)

        if len(df) < 1:
            return TradeSignal(Signal.HOLD, df.iloc[-1]["close"] if len(df) else 0, "Dados insuficientes")

        curr = df.iloc[-1]
        price = curr["close"]

        if price > curr["breakout_high"]:
            log.info(f"COMPRA | rompimento acima de {curr['breakout_high']:.4f} (janela {self.window})")
            return TradeSignal(Signal.BUY, price, f"Rompimento acima da maxima de {self.window} periodos ({curr['breakout_high']:.4f})")

        if price < curr["breakout_low"]:
            log.info(f"VENDA | rompimento abaixo de {curr['breakout_low']:.4f} (janela {self.window})")
            return TradeSignal(Signal.SELL, price, f"Rompimento abaixo da minima de {self.window} periodos ({curr['breakout_low']:.4f})")

        return TradeSignal(Signal.HOLD, price, f"Dentro da faixa ({curr['breakout_low']:.4f} - {curr['breakout_high']:.4f})")
