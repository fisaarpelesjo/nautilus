"""H27 -- meta-labeling: pré-condição sobre o sinal primário (spec 064)."""
import pandas as pd
import pytest

from strategy.base import Signal


def test_resumo_conta_alvo_stop_tempo_pelo_rotulo_bruto():
    from backtesting.meta_labeling import _resumo
    from strategy.barreira_tripla import ParametrosBarreira

    rot = pd.Series([1, -1, -1, 1, 1, 0])  # alvo, stop, stop, alvo, alvo, tempo

    f = _resumo(rot, "teste", ParametrosBarreira())

    assert f.n == 6
    assert f.alvo == 3
    assert f.stop == 2
    assert f.tempo == 1
    assert f.razao == pytest.approx(1.5)


def test_resumo_stop_zero_produz_razao_infinita_sem_quebrar():
    from backtesting.meta_labeling import _resumo
    from strategy.barreira_tripla import ParametrosBarreira

    rot = pd.Series([1, 1, 0])

    f = _resumo(rot, "teste", ParametrosBarreira())

    assert f.razao == float("inf")
    assert f.supera_empate is False  # sem stop, supera_empate_com_confianca nao roda


def test_avaliar_precondicao_atendida_quando_entrada_supera_empate(monkeypatch):
    """Amostra grande e razao alta nos eventos de entrada -- precondicao
    atendida (mesmo padrao de M9/M13: precisa de amostra, nao so razao)."""
    import backtesting.meta_labeling as mod

    idx = pd.date_range("2026-01-01", periods=3000, freq="4h")
    # entrada primaria (onde o sinal == BUY, os primeiros 1000 candles):
    # razao bem acima do empate, amostra grande.
    rot_entrada = pd.Series([1] * 700 + [-1] * 300, index=idx[:1000])
    # resto (fora do sinal primario): irrelevante para este teste, so precisa
    # existir para compor o baseline sem quebrar.
    rot_resto = pd.Series([1] * 250 + [-1] * 250, index=idx[1000:1500])

    sinais = pd.Series(Signal.HOLD, index=idx)
    sinais.iloc[:1000] = Signal.BUY

    def _fake_fetch(par, timeframe, limit):
        return pd.DataFrame({"close": range(len(idx))}, index=idx)

    def _fake_preparar(df, estrategia):
        return df

    def _fake_precompute(prep, estrategia):
        return sinais.loc[prep.index]

    def _fake_rotular(prep, params):
        rot_completo = pd.concat([rot_entrada, rot_resto])
        rot_completo = rot_completo.reindex(idx)
        return pd.DataFrame({"rotulo_bruto": rot_completo})

    monkeypatch.setattr(mod, "fetch_ohlcv", _fake_fetch)
    monkeypatch.setattr(mod, "preparar", _fake_preparar)
    monkeypatch.setattr(mod, "precompute_signals", _fake_precompute)
    monkeypatch.setattr(mod, "rotular", _fake_rotular)

    r = mod.avaliar_precondicao(pares=["FAKE/USDT"])

    assert r.entrada_primaria.n == 1000
    assert r.entrada_primaria.alvo == 700
    assert r.entrada_primaria.stop == 300
    assert r.precondicao_atendida is True


def test_avaliar_precondicao_nao_atendida_quando_entrada_perto_do_empate(monkeypatch):
    """Espelha o achado real medido: razao de entrada ~0.50, empate 0.50,
    amostra n~740 -- nao sobrevive ao IC de Wilson."""
    import backtesting.meta_labeling as mod

    idx = pd.date_range("2026-01-01", periods=1000, freq="4h")
    rot_entrada_vals = [1] * 227 + [-1] * 453 + [0] * 60
    rot_geral = pd.Series(rot_entrada_vals, index=idx[:len(rot_entrada_vals)])

    sinais = pd.Series(Signal.BUY, index=idx[:len(rot_entrada_vals)])

    def _fake_fetch(par, timeframe, limit):
        return pd.DataFrame({"close": range(len(idx))}, index=idx)

    def _fake_preparar(df, estrategia):
        return df.loc[idx[:len(rot_entrada_vals)]]

    def _fake_precompute(prep, estrategia):
        return sinais.loc[prep.index]

    def _fake_rotular(prep, params):
        return pd.DataFrame({"rotulo_bruto": rot_geral})

    monkeypatch.setattr(mod, "fetch_ohlcv", _fake_fetch)
    monkeypatch.setattr(mod, "preparar", _fake_preparar)
    monkeypatch.setattr(mod, "precompute_signals", _fake_precompute)
    monkeypatch.setattr(mod, "rotular", _fake_rotular)

    r = mod.avaliar_precondicao(pares=["FAKE/USDT"])

    assert r.entrada_primaria.alvo == 227
    assert r.entrada_primaria.stop == 453
    assert r.precondicao_atendida is False


def test_avaliar_precondicao_pula_pares_sem_prep(monkeypatch):
    import backtesting.meta_labeling as mod

    idx = pd.date_range("2026-01-01", periods=100, freq="4h")

    def _fake_fetch(par, timeframe, limit):
        return pd.DataFrame({"close": range(len(idx))}, index=idx)

    def _fake_preparar(df, estrategia):
        return None  # simula prep insuficiente

    monkeypatch.setattr(mod, "fetch_ohlcv", _fake_fetch)
    monkeypatch.setattr(mod, "preparar", _fake_preparar)

    with pytest.raises(ValueError):
        mod.avaliar_precondicao(pares=["FAKE/USDT"])


def test_avaliar_precondicao_usa_pares_passados_nao_universo_default(monkeypatch):
    import backtesting.meta_labeling as mod

    idx = pd.date_range("2026-01-01", periods=50, freq="4h")
    chamados = []

    def _fake_fetch(par, timeframe, limit):
        chamados.append(par)
        return pd.DataFrame({"close": range(len(idx))}, index=idx)

    def _fake_preparar(df, estrategia):
        return df

    def _fake_precompute(prep, estrategia):
        return pd.Series(Signal.HOLD, index=prep.index)

    def _fake_rotular(prep, params):
        return pd.DataFrame({"rotulo_bruto": pd.Series([1, -1] * (len(idx) // 2), index=idx)})

    monkeypatch.setattr(mod, "fetch_ohlcv", _fake_fetch)
    monkeypatch.setattr(mod, "preparar", _fake_preparar)
    monkeypatch.setattr(mod, "precompute_signals", _fake_precompute)
    monkeypatch.setattr(mod, "rotular", _fake_rotular)

    mod.avaliar_precondicao(pares=["A/USDT", "B/USDT"])

    assert chamados == ["A/USDT", "B/USDT"]
