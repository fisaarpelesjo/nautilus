import pandas as pd
from strategy.base import BaseStrategy, Signal, TradeSignal


class DayFilterStrategy(BaseStrategy):
    """
    Wrapper generico: delega indicadores/sinal a uma estrategia base e
    suspende apenas novas entradas (BUY) em dias da semana bloqueados.
    Sinal de venda de posicao ja aberta nunca e bloqueado (mesma convencao
    dos demais filtros de entrada do projeto).

    blocked_weekdays usa a convencao pandas.Timestamp.dayofweek: 0=segunda
    ... 4=sexta, 5=sabado, 6=domingo.
    """

    def __init__(self, base_strategy: BaseStrategy, blocked_weekdays: list):
        self.base_strategy = base_strategy
        self.blocked_weekdays = set(blocked_weekdays)
        self.name = f"{getattr(base_strategy, 'name', type(base_strategy).__name__)}+DayFilter{sorted(blocked_weekdays)}"

    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        return self.base_strategy.calculate_indicators(df)

    # Generico o bastante para cobrir o warmup de qualquer estrategia usada
    # no projeto (EMA_TREND=50, ADX 14x2, Breakout ate janela 200 fica de
    # fora deste wrapper especifico, mas RSI/BB/EMA cabem folgados). Sem este
    # guard, o caminho lento de generate_signal por candle (ativado porque
    # este wrapper nao expoe `.params` para o atalho vetorizado de
    # precompute_signals) chama calculate_indicators em janelas minusculas
    # geradas por simulate_backtest(start_index=0) na fatia de confirmacao,
    # e estrategias como EmaRsiStrategy calculam ADX/RSI sem checar o
    # tamanho antes, estourando index-out-of-bounds.
    _MIN_WARMUP_ROWS = 60

    def generate_signal(self, df: pd.DataFrame) -> TradeSignal:
        if len(df) < self._MIN_WARMUP_ROWS:
            price = df.iloc[-1]["close"] if len(df) else 0
            return TradeSignal(Signal.HOLD, price, "Dados insuficientes (warmup)")

        signal = self.base_strategy.generate_signal(df)
        if signal.signal != Signal.BUY or len(df) == 0:
            return signal

        weekday = df.index[-1].dayofweek
        if weekday in self.blocked_weekdays:
            return TradeSignal(
                Signal.HOLD,
                signal.price,
                f"Entrada suspensa: dia da semana bloqueado (weekday={weekday}) | sinal original: {signal.reason}",
            )
        return signal
