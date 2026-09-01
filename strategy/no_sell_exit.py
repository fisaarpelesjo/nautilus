import pandas as pd

from strategy.base import BaseStrategy, Signal, TradeSignal


class NoSellExitStrategy(BaseStrategy):
    """Wrapper: mantem as entradas da estrategia base e suprime o sinal de SELL.

    Hipotese que motiva o wrapper: nos 28 trades de paper acumulados ate
    2026-09-01, a saida por "Sinal de venda" foi a pior das tres -- -4,93 por
    trade em 6 trades, contra -2,09 do Stop Loss e +7,44 do Take Profit. Ou
    seja, o cruzamento de EMA para baixo estaria tirando a posicao antes do que
    o stop tiraria, transformando recuo em prejuizo realizado.

    Com o SELL suprimido, a posicao so sai por stop loss, trailing stop ou take
    profit -- os tres geridos por `trading/position_lifecycle.py`, nao pela
    estrategia. Se a tese estiver certa, o resultado melhora; se estiver errada,
    piora, porque o cruzamento estava protegendo de quedas maiores.

    Nao e uma estrategia para operar: e um instrumento de medicao. Comparar com
    a base isola o efeito de uma unica decisao.
    """

    def __init__(self, base_strategy: BaseStrategy):
        self.base_strategy = base_strategy
        base_nome = getattr(base_strategy, "name", type(base_strategy).__name__)
        self.name = f"{base_nome}+SemSaidaSELL"

    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        return self.base_strategy.calculate_indicators(df)

    # Mesmo guard do DayFilterStrategy e pela mesma razao: sem `.params`, este
    # wrapper cai no caminho por candle de precompute_signals, que chama
    # calculate_indicators em janelas minusculas na fatia de confirmacao.
    _MIN_WARMUP_ROWS = 60

    def generate_signal(self, df: pd.DataFrame) -> TradeSignal:
        if len(df) < self._MIN_WARMUP_ROWS:
            price = df.iloc[-1]["close"] if len(df) else 0
            return TradeSignal(Signal.HOLD, price, "Dados insuficientes (warmup)")

        signal = self.base_strategy.generate_signal(df)
        if signal.signal != Signal.SELL:
            return signal

        return TradeSignal(
            Signal.HOLD,
            signal.price,
            f"Saida por SELL suprimida (sai so por stop/trailing/TP) | sinal original: {signal.reason}",
        )
