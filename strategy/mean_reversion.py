import pandas as pd
import ta
from strategy.base import BaseStrategy, Signal, TradeSignal
from utils.logger import get_logger

log = get_logger("mean_reversion")


class MeanReversionStrategy(BaseStrategy):
    """
    Reversao a media via Bollinger Bands + RSI: compra quando o preco toca
    a banda inferior com RSI em sobrevenda (esticado para baixo, espera-se
    retorno a media), vende quando o preco volta a cruzar a banda media
    (reversao concluida) ou o RSI entra em sobrecompra.

    Oposto do EMA/RSI (trend-following): esta estrategia aposta contra o
    movimento em vez de na continuacao dele, o que a torna candidata natural
    para regime de mercado lateral/choppy, onde trend-following struggle.

    Filtro de regime via ADX opcional (`adx_filter_enabled`): mean-reversion
    perde dinheiro justamente nos dias em que o mercado sai da lateralizacao
    e entra em tendencia forte -- o preco "esticado" continua esticando em
    vez de reverter. ADX baixo (< adx_threshold) indica ausencia de tendencia
    forte, contexto favoravel a reversao; ADX alto suspende novas entradas.
    Polaridade invertida em relacao ao filtro de regime do EMA/RSI (que
    suspende em ADX baixo -- la o filtro busca tendencia, aqui busca lateral).
    """

    def __init__(self, rsi_period: int = 14, rsi_oversold: int = 30,
                 rsi_overbought: int = 70, bb_period: int = 20, bb_std: float = 2.0,
                 adx_filter_enabled: bool = False, adx_threshold: float = 20.0,
                 adx_period: int = 14):
        self.rsi_period = rsi_period
        self.rsi_oversold = rsi_oversold
        self.rsi_overbought = rsi_overbought
        self.bb_period = bb_period
        self.bb_std = bb_std
        self.adx_filter_enabled = adx_filter_enabled
        self.adx_threshold = adx_threshold
        self.adx_period = adx_period

    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        df["rsi"] = ta.momentum.RSIIndicator(df["close"], window=self.rsi_period).rsi()
        bb = ta.volatility.BollingerBands(df["close"], window=self.bb_period, window_dev=self.bb_std)
        df["bb_upper"] = bb.bollinger_hband()
        df["bb_middle"] = bb.bollinger_mavg()
        df["bb_lower"] = bb.bollinger_lband()
        if self.adx_filter_enabled:
            df["adx"] = ta.trend.ADXIndicator(df["high"], df["low"], df["close"], window=self.adx_period).adx()
        df.dropna(inplace=True)
        return df

    def generate_signal(self, df: pd.DataFrame) -> TradeSignal:
        min_rows = max(self.bb_period, self.rsi_period, self.adx_period * 2 if self.adx_filter_enabled else 0) + 1
        if len(df) < min_rows:
            return TradeSignal(Signal.HOLD, df.iloc[-1]["close"] if len(df) else 0, "Dados insuficientes")

        df = self.calculate_indicators(df)

        if len(df) < 1:
            return TradeSignal(Signal.HOLD, df.iloc[-1]["close"] if len(df) else 0, "Dados insuficientes")

        curr = df.iloc[-1]
        price = curr["close"]
        rsi = curr["rsi"]

        # ADX filtra so novas entradas -- sinal de venda de posicao ja aberta
        # nunca e bloqueado (mesma convencao do filtro de regime do EMA/RSI).
        adx_blocks_entry = self.adx_filter_enabled and curr["adx"] >= self.adx_threshold

        if not adx_blocks_entry and price <= curr["bb_lower"] and rsi < self.rsi_oversold:
            log.info(f"COMPRA | preco na banda inferior ({curr['bb_lower']:.4f}) | RSI={rsi:.1f} sobrevenda")
            return TradeSignal(Signal.BUY, price, f"Reversao a media: preco <= BB inferior + RSI={rsi:.1f} sobrevenda")

        if price >= curr["bb_middle"] or rsi > self.rsi_overbought:
            log.info(f"VENDA | reversao concluida (preco={price:.4f}, media={curr['bb_middle']:.4f}) | RSI={rsi:.1f}")
            return TradeSignal(Signal.SELL, price, f"Reversao concluida: preco >= BB media ou RSI={rsi:.1f} sobrecompra")

        if adx_blocks_entry:
            return TradeSignal(Signal.HOLD, price, f"ADX={curr['adx']:.1f} -- tendencia forte, entradas de reversao suspensas")

        return TradeSignal(Signal.HOLD, price, f"Aguardando extremo (RSI={rsi:.1f}, BB {curr['bb_lower']:.4f}-{curr['bb_upper']:.4f})")
