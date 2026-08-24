"""MIN_PRICE_USDT no backtest (candidata 021 do BACKLOG).

`trading/runner.py` descarta pares abaixo de MIN_PRICE_USDT ANTES de avaliar o
sinal, mas `backtesting/engine.py` nao tinha filtro equivalente: o par passava no
backtest com numeros normais e nunca operava em producao.

Foi assim que LUNC/USDT ficou 8 dias em PAIRS sem gerar uma unica decisao --
e como era PAIRS[0], alvo padrao de `backtest`/`edge`/`chart`, vereditos daquele
periodo foram calculados sobre um par que o bot nunca operou.
"""
import pandas as pd

from backtesting import engine
from backtesting.approval import evaluate_approval
from backtesting.engine import run_backtest
from strategy.base import Signal, TradeSignal


class _FlatStrategy:
    def calculate_indicators(self, df):
        return df

    def generate_signal(self, _df):
        return TradeSignal(Signal.HOLD, 1.0, "test")


def _df(preco):
    idx = pd.date_range("2026-01-01", periods=150, freq="h")
    return pd.DataFrame({
        "open": [preco] * 150, "high": [preco] * 150,
        "low": [preco] * 150, "close": [preco] * 150,
        "volume": [1.0] * 150, "atr": [preco * 0.01] * 150,
    }, index=idx)


def test_backtest_flags_pair_below_min_price(monkeypatch):
    monkeypatch.setattr(engine, "MIN_PRICE_USDT", 0.001)
    monkeypatch.setattr(engine, "fetch_ohlcv", lambda s, tf, limit=None: _df(0.0000572))
    monkeypatch.setattr(engine, "print_report", lambda r: None)

    result = run_backtest("LUNC/USDT", "4h", strategy=_FlatStrategy())

    assert result.below_min_price is True


def test_backtest_does_not_flag_normal_pair(monkeypatch):
    monkeypatch.setattr(engine, "MIN_PRICE_USDT", 0.001)
    monkeypatch.setattr(engine, "fetch_ohlcv", lambda s, tf, limit=None: _df(65000.0))
    monkeypatch.setattr(engine, "print_report", lambda r: None)

    result = run_backtest("BTC/USDT", "4h", strategy=_FlatStrategy())

    assert result.below_min_price is False


def test_verdict_is_inconclusive_for_untradable_pair(monkeypatch):
    # Numeros que passariam em TODOS os criterios normais -- o veredito ainda
    # tem que ser inconclusivo, porque o bot nunca opera este par.
    monkeypatch.setattr(engine, "MIN_PRICE_USDT", 0.001)
    monkeypatch.setattr(engine, "fetch_ohlcv", lambda s, tf, limit=None: _df(0.0000572))
    monkeypatch.setattr(engine, "print_report", lambda r: None)
    result = run_backtest("LUNC/USDT", "4h", strategy=_FlatStrategy())
    result.total_trades = 50
    result.profit_factor = 9.0
    result.total_return_pct = 80.0
    result.buy_hold_return_pct = 1.0
    result.max_drawdown_pct = 1.0

    verdict = evaluate_approval(result)

    assert verdict.status == "inconclusivo"
    assert any("MIN_PRICE_USDT" in r for r in verdict.reasons)


def test_verdict_untradable_takes_precedence_over_approval(monkeypatch):
    # Ordem importa: a checagem de par inoperavel vem ANTES das de qualidade,
    # senao um par abaixo do minimo com bons numeros sairia "aprovado".
    monkeypatch.setattr(engine, "MIN_PRICE_USDT", 0.001)
    monkeypatch.setattr(engine, "fetch_ohlcv", lambda s, tf, limit=None: _df(0.0000572))
    monkeypatch.setattr(engine, "print_report", lambda r: None)
    result = run_backtest("LUNC/USDT", "4h", strategy=_FlatStrategy())
    result.total_trades = 50
    result.profit_factor = 9.0
    result.total_return_pct = 80.0
    result.buy_hold_return_pct = 1.0
    result.max_drawdown_pct = 1.0

    assert evaluate_approval(result).status != "aprovado"
