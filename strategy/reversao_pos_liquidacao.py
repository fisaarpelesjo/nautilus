"""H34 -- reversao pos-liquidacao (spec 070). Sinal de entrada experimental
de PESQUISA, mesmo padrao de `strategy/breakout.py`: nao e usado por
`trading/runner.py` nem `backtesting/engine.py::run_backtest` por omissao.

Proxy de cascata de liquidacao forcada via OHLCV puro (Binance nao publica
historico livre de `forceOrder`) -- ver
`specs/070-h34-reversao-pos-liquidacao/research.md` para D1/D2 declarados
antes de qualquer medicao real:

D1: pavio inferior (`min(open, close) - low`) >= 50% do range do candle
(`high - low`).

D2: volume >= 3x a media movel de `JANELA_MEDIA_VOLUME` candles -- janela
propria deste modulo, desacoplada de `VOLUME_MA_PERIOD` de producao para
que mudar a config de producao nao mude silenciosamente este resultado ja
medido.

Mais fechamento de recuperacao (`close > open`) -- sem os tres criterios
simultaneos, nao e o padrao declarado. Sem SELL proprio: a saida fica a
cargo do SL/TP/trailing por ATR ja generico em
`backtesting.engine.simulate_backtest`.
"""
import pandas as pd
import ta

from strategy.base import BaseStrategy, Signal, TradeSignal

LIMIAR_PAVIO_FRACAO_RANGE = 0.5   # D1
LIMIAR_VOLUME_MULTIPLICADOR = 3.0  # D2
JANELA_MEDIA_VOLUME = 20


class ReversaoPosLiquidacaoStrategy(BaseStrategy):
    """Compra quando um candle bate o proxy pavio+volume+recuperacao (D1/D2).
    Nunca gera SELL -- saida via SL/TP/trailing ATR do motor de backtest.
    """

    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        df["volume_ma"] = df["volume"].rolling(window=JANELA_MEDIA_VOLUME).mean()
        df["atr"] = ta.volatility.AverageTrueRange(
            df["high"], df["low"], df["close"], window=14
        ).average_true_range()
        return df

    def generate_signal(self, df: pd.DataFrame) -> TradeSignal:
        if len(df) < max(JANELA_MEDIA_VOLUME, 14) + 1:
            return TradeSignal(Signal.HOLD, df.iloc[-1]["close"] if len(df) else 0, "Dados insuficientes")

        df = self.calculate_indicators(df)
        curr = df.iloc[-1]
        price = curr["close"]

        if pd.isna(curr["volume_ma"]):
            return TradeSignal(Signal.HOLD, price, "Media de volume ainda em warmup")

        candle_range = curr["high"] - curr["low"]
        if candle_range <= 0:
            return TradeSignal(Signal.HOLD, price, "Candle sem range (high == low)")

        pavio_inferior = min(curr["open"], curr["close"]) - curr["low"]
        pavio_ok = (pavio_inferior / candle_range) >= LIMIAR_PAVIO_FRACAO_RANGE
        volume_ok = curr["volume"] >= curr["volume_ma"] * LIMIAR_VOLUME_MULTIPLICADOR
        recuperacao_ok = curr["close"] > curr["open"]

        if pavio_ok and volume_ok and recuperacao_ok:
            return TradeSignal(
                Signal.BUY, price,
                f"Proxy reversao pos-liquidacao: pavio {pavio_inferior / candle_range:.0%} do range, "
                f"volume {curr['volume'] / curr['volume_ma']:.1f}x a media",
            )

        return TradeSignal(Signal.HOLD, price, "Padrao pavio+volume+recuperacao nao confirmado")
