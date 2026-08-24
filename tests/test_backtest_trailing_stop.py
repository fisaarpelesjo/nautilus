"""Trailing stop no motor de backtest.

Achado metodologico (2026-08-24): `simulate_backtest` usava um stop FIXO
calculado na entrada, enquanto `trading/position_lifecycle.py`
`handle_open_position()` move o stop para cima a cada novo maximo. Backtest e
producao mediam estrategias diferentes -- e todas as decisoes de par/parametro
do projeto foram tomadas com a regua errada.

A assinatura da divergencia nos dados reais: 3 trades fecharam por "Stop Loss"
COM LUCRO (ORCA +$0.35, ACE +$2.04, PLUME +$0.43), resultado impossivel sob
stop fixo, onde o stop esta sempre abaixo da entrada.
"""
import pandas as pd
import pytest

from backtesting.engine import simulate_backtest
from strategy.base import Signal, TradeSignal


class SequenceStrategy:
    def __init__(self, signals):
        self.signals = list(signals)

    def generate_signal(self, _df):
        if self.signals:
            return TradeSignal(self.signals.pop(0), 100.0, "test")
        return TradeSignal(Signal.HOLD, 100.0, "test")


def _df(rows):
    index = pd.date_range("2026-01-01", periods=len(rows), freq="h")
    return pd.DataFrame(rows, index=index)


def test_trailing_stop_can_close_above_entry_price():
    # ATR=2, multiplicador 1.5 -> stop inicial em 100 - 3 = 97.
    # Candle 3 sobe ate 120: trailing puxa o stop para 120 - 3 = 117.
    # Candle 4 recua ate 110: bate o stop JA MOVIDO, fechando ACIMA da entrada.
    # Com stop fixo (comportamento antigo) esse trade nunca fecharia em 117.
    data = _df([
        {"open": 100.0, "high": 100.0, "low": 100.0, "close": 100.0, "volume": 1.0, "atr": 2.0},
        {"open": 100.0, "high": 100.0, "low": 100.0, "close": 100.0, "volume": 1.0, "atr": 2.0},
        {"open": 100.0, "high": 120.0, "low": 100.0, "close": 118.0, "volume": 1.0, "atr": 2.0},
        {"open": 118.0, "high": 118.0, "low": 110.0, "close": 112.0, "volume": 1.0, "atr": 2.0},
    ])
    strategy = SequenceStrategy([Signal.BUY, Signal.HOLD, Signal.HOLD])

    result = simulate_backtest(data, strategy, start_index=1, fee_rate=0.0, slippage_pct=0.0,
                                atr_sl_multiplier=1.5, atr_tp_multiplier=100.0)

    assert result.total_trades == 1
    trade = result.trades[0]
    assert trade.exit_reason == "Stop Loss"
    assert trade.exit_price == pytest.approx(117.0)
    assert trade.pnl > 0, "trailing stop deve permitir saida por Stop Loss com lucro"


def test_trailing_stop_never_moves_down():
    # Candle 3 sobe (stop sobe para 117), candle 4 cai sem bater o stop, candle 5
    # sobe menos que o topo anterior -- o stop tem que continuar em 117, nunca
    # recuar para o nivel da entrada.
    data = _df([
        {"open": 100.0, "high": 100.0, "low": 100.0, "close": 100.0, "volume": 1.0, "atr": 2.0},
        {"open": 100.0, "high": 100.0, "low": 100.0, "close": 100.0, "volume": 1.0, "atr": 2.0},
        {"open": 100.0, "high": 120.0, "low": 100.0, "close": 119.0, "volume": 1.0, "atr": 2.0},
        {"open": 119.0, "high": 119.0, "low": 118.0, "close": 118.5, "volume": 1.0, "atr": 2.0},
        {"open": 118.5, "high": 118.6, "low": 116.0, "close": 117.0, "volume": 1.0, "atr": 2.0},
    ])
    strategy = SequenceStrategy([Signal.BUY, Signal.HOLD, Signal.HOLD, Signal.HOLD])

    result = simulate_backtest(data, strategy, start_index=1, fee_rate=0.0, slippage_pct=0.0,
                                atr_sl_multiplier=1.5, atr_tp_multiplier=100.0)

    assert result.total_trades == 1
    # Fecha no candle 5 (low 116 <= stop 117), no stop preservado do topo anterior.
    assert result.trades[0].exit_price == pytest.approx(117.0)


def test_stop_checked_before_trailing_update_within_same_candle():
    # Candle 3 tem maxima 120 E minima 96 -- OHLCV nao diz qual veio primeiro.
    # A escolha conservadora e assumir o movimento adverso primeiro: o stop
    # vigente no inicio do candle (97) dispara, em vez de o trailing subir para
    # 117 e so entao stopar.
    data = _df([
        {"open": 100.0, "high": 100.0, "low": 100.0, "close": 100.0, "volume": 1.0, "atr": 2.0},
        {"open": 100.0, "high": 100.0, "low": 100.0, "close": 100.0, "volume": 1.0, "atr": 2.0},
        {"open": 100.0, "high": 120.0, "low": 96.0, "close": 118.0, "volume": 1.0, "atr": 2.0},
    ])
    strategy = SequenceStrategy([Signal.BUY, Signal.HOLD])

    result = simulate_backtest(data, strategy, start_index=1, fee_rate=0.0, slippage_pct=0.0,
                                atr_sl_multiplier=1.5, atr_tp_multiplier=100.0)

    assert result.total_trades == 1
    assert result.trades[0].exit_price == pytest.approx(97.0)
    assert result.trades[0].pnl < 0


def test_no_trailing_without_atr():
    # ATR=0 cai no fallback percentual (STOP_LOSS_PCT) e nao deve trailar --
    # mesma condicao `pos.atr > 0` que handle_open_position() exige.
    data = _df([
        {"open": 100.0, "high": 100.0, "low": 100.0, "close": 100.0, "volume": 1.0, "atr": 0.0},
        {"open": 100.0, "high": 100.0, "low": 100.0, "close": 100.0, "volume": 1.0, "atr": 0.0},
        {"open": 100.0, "high": 130.0, "low": 100.0, "close": 128.0, "volume": 1.0, "atr": 0.0},
        {"open": 128.0, "high": 128.0, "low": 120.0, "close": 121.0, "volume": 1.0, "atr": 0.0},
    ])
    strategy = SequenceStrategy([Signal.BUY, Signal.HOLD, Signal.HOLD])

    result = simulate_backtest(data, strategy, start_index=1, fee_rate=0.0, slippage_pct=0.0,
                                stop_loss_pct=0.015, atr_tp_multiplier=100.0, take_profit_pct=10.0)

    # Sem trailing, o stop fica em 98.5 e o trade nao fecha por stop nestes candles.
    assert result.trades[0].exit_reason == "Fim do periodo"
