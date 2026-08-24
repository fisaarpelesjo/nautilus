"""MTF point-in-time (`as_of`) para simulacao sobre historico.

Achado 2026-08-24: `mtf_confirmed()` buscava sempre o candle MTF mais recente.
Em producao isso e o correto; em `trading/replay.py`, que roda sobre candles
antigos, significava comparar o preco HISTORICO contra a EMA de tendencia de
HOJE -- um filtro deterministico baseado no futuro.

O vies era direcional, nao ruido: num par que subiu, toda entrada antiga (preco
baixo) ficava abaixo da EMA atual e era bloqueada -- justamente as entradas
baratas, que tendem a ser as vencedoras. Caso real medido em NIL/USDT: o replay
descartou o trade de +$17,36 e manteve o de -$8,24.
"""
import pandas as pd

from trading import position_lifecycle


class _TrendStrategy:
    """ema_trend = media das closes da janela recebida -- deixa o corte por
    `as_of` visivel no resultado."""

    def calculate_indicators(self, df):
        return df.assign(ema_trend=df["close"].expanding().mean())


def _daily_df():
    # Preco sobe ao longo do tempo: a EMA "de hoje" fica bem acima dos precos antigos.
    idx = pd.date_range("2026-01-01", periods=10, freq="D")
    return pd.DataFrame({"close": [10.0 * (i + 1) for i in range(10)]}, index=idx)


def test_mtf_without_as_of_uses_latest_candle(monkeypatch):
    monkeypatch.setattr(position_lifecycle, "fetch_ohlcv", lambda s, tf: _daily_df())
    # media das 10 closes (10..100) = 55. Producao compara contra o candle atual.
    assert position_lifecycle.mtf_confirmed("X/USDT", 60.0, _TrendStrategy()) is True
    assert position_lifecycle.mtf_confirmed("X/USDT", 50.0, _TrendStrategy()) is False


def test_mtf_with_as_of_ignores_future_candles(monkeypatch):
    monkeypatch.setattr(position_lifecycle, "fetch_ohlcv", lambda s, tf: _daily_df())
    # Cortando em 03/01, so as closes 10,20,30 contam -> media 20.
    # Um preco de 25 era ACIMA da tendencia naquela data, mesmo estando bem
    # abaixo da media de hoje (55) -- que e exatamente o trade que o vies
    # antigo descartava.
    as_of = pd.Timestamp("2026-01-03")

    assert position_lifecycle.mtf_confirmed("X/USDT", 25.0, _TrendStrategy(), as_of=as_of) is True
    # E sem o corte, o mesmo preco seria bloqueado:
    assert position_lifecycle.mtf_confirmed("X/USDT", 25.0, _TrendStrategy()) is False


def test_mtf_as_of_before_any_candle_fails_closed(monkeypatch):
    monkeypatch.setattr(position_lifecycle, "fetch_ohlcv", lambda s, tf: _daily_df())
    # Nenhum candle MTF anterior a essa data -- desconhecido bloqueia, mesma
    # politica do except.
    as_of = pd.Timestamp("2025-01-01")

    assert position_lifecycle.mtf_confirmed("X/USDT", 999.0, _TrendStrategy(), as_of=as_of) is False


def test_mtf_as_of_still_fails_closed_on_network_error(monkeypatch):
    monkeypatch.setattr(
        position_lifecycle, "fetch_ohlcv",
        lambda s, tf: (_ for _ in ()).throw(RuntimeError("timeout")),
    )

    assert position_lifecycle.mtf_confirmed(
        "X/USDT", 100.0, _TrendStrategy(), as_of=pd.Timestamp("2026-01-05")
    ) is False
