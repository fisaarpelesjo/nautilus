import pandas as pd
import pytest
import requests

from backtesting import dvol_gate as mod
from data import deribit


class _FakeResponse:
    def __init__(self, json_data, status_code=200):
        self._json_data = json_data
        self.status_code = status_code

    def json(self):
        return self._json_data

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(f"HTTP {self.status_code}")


def _ok_body(pontos):
    return {"jsonrpc": "2.0", "result": {"data": pontos, "continuation": None}}


def test_fetch_dvol_history_parses_valid_response(monkeypatch):
    pontos = [[1710892800000, 76.0, 79.0, 75.0, 77.0], [1710979200000, 77.0, 80.0, 76.0, 78.0]]
    monkeypatch.setattr(deribit.requests, "get", lambda url, params=None, timeout=None: _FakeResponse(_ok_body(pontos)))

    df = deribit.fetch_dvol_history("BTC")

    assert list(df["close"]) == [77.0, 78.0]
    assert df.index.is_monotonic_increasing
    assert not df.index.has_duplicates


def test_fetch_dvol_history_raises_on_network_failure(monkeypatch):
    def _get(url, params=None, timeout=None):
        raise requests.ConnectionError("timeout simulado")

    monkeypatch.setattr(deribit.requests, "get", _get)

    with pytest.raises(requests.ConnectionError):
        deribit.fetch_dvol_history("BTC")


def test_fetch_dvol_history_raises_quando_resposta_sem_result(monkeypatch):
    monkeypatch.setattr(deribit.requests, "get",
                         lambda url, params=None, timeout=None: _FakeResponse({"error": "algo deu errado"}))

    with pytest.raises(RuntimeError):
        deribit.fetch_dvol_history("BTC")


def test_alinhar_causal_usa_valor_do_dia_anterior():
    dvol = pd.Series([70.0, 80.0, 90.0], index=pd.date_range("2026-01-01", periods=3, freq="D", tz="UTC"))
    evento_meio_dia = pd.DatetimeIndex(["2026-01-02 12:00:00"])

    resultado = mod._alinhar_causal(evento_meio_dia, dvol)

    assert resultado.iloc[0] == pytest.approx(70.0)


def test_alinhar_causal_buraco_interno_na_serie_e_nan_nunca_valor_antigo():
    # 01-03 ausente (buraco interno, nao limite de retencao) -- evento em
    # 01-04 precisa do D-1 = 01-03, que nao existe. Nunca deve reusar o
    # valor mais antigo (01-02 = 80.0) como se fosse o de 01-03.
    dvol = pd.Series(
        [70.0, 80.0, 999.0],
        index=pd.DatetimeIndex(["2026-01-01", "2026-01-02", "2026-01-04"], tz="UTC"),
    )
    evento = pd.DatetimeIndex(["2026-01-04 06:00:00"])

    resultado = mod._alinhar_causal(evento, dvol)

    assert pd.isna(resultado.iloc[0])


def test_alinhar_causal_sem_dvol_disponivel_e_nan():
    dvol = pd.Series([70.0], index=pd.DatetimeIndex(["2026-06-01"], tz="UTC"))
    evento_antigo = pd.DatetimeIndex(["2026-01-01 06:00:00"])

    resultado = mod._alinhar_causal(evento_antigo, dvol)

    assert pd.isna(resultado.iloc[0])


def test_resumo_calcula_razao_e_significancia():
    rot = pd.Series([1, 1, -1, 1, -1, -1, 0])  # alvo=3, stop=3, tempo=1

    resumo = mod._resumo(rot, "teste", mod.ParametrosBarreira())

    assert resumo.n == 7
    assert resumo.alvo == 3
    assert resumo.stop == 3
    assert resumo.razao == pytest.approx(1.0)


def test_avaliar_precondicao_dvol_exclui_eventos_sem_dvol_alinhavel(monkeypatch):
    idx = pd.date_range("2026-06-01", periods=200, freq="4h")
    prep = pd.DataFrame({
        "close": 100.0, "high": 101.0, "low": 99.0, "atr": 2.0,
    }, index=idx)

    # dvol so existe a partir do MEIO do periodo -- metade dos eventos fica sem DVOL alinhavel
    dvol = pd.Series([50.0] * 50, index=pd.date_range("2026-06-15", periods=50, freq="D", tz="UTC"))
    monkeypatch.setattr(mod, "fetch_dvol_history", lambda currency: pd.DataFrame({"close": dvol}))
    monkeypatch.setattr(mod, "fetch_ohlcv", lambda par, tf, limit: prep)
    monkeypatch.setattr(mod, "preparar", lambda df, estrategia: prep)
    monkeypatch.setattr(mod, "precompute_signals",
                         lambda p, estrategia: pd.Series(mod.Signal.BUY, index=p.index))
    monkeypatch.setattr(mod, "rotular",
                         lambda p, params: pd.DataFrame({"rotulo_bruto": [1.0] * len(p)}, index=p.index))
    monkeypatch.setattr(mod, "avaliar_precondicao",
                         lambda pares, params: "baseline-fake")

    resultado = mod.avaliar_precondicao_dvol(["BTC/USDT"])

    # eventos antes de 2026-06-15 (sem DVOL) foram excluidos -- so contam
    # os que caem dentro da janela real de dvol
    assert resultado.dvol_alto.n + resultado.resto.n < len(idx)
    assert resultado.baseline_h27 == "baseline-fake"


def test_avaliar_precondicao_dvol_pula_par_sem_evento_com_dvol(monkeypatch):
    idx = pd.date_range("2026-01-01", periods=50, freq="4h")
    prep = pd.DataFrame({"close": 100.0, "high": 101.0, "low": 99.0, "atr": 2.0}, index=idx)

    dvol = pd.Series([50.0] * 10, index=pd.date_range("2027-01-01", periods=10, freq="D", tz="UTC"))
    monkeypatch.setattr(mod, "fetch_dvol_history", lambda currency: pd.DataFrame({"close": dvol}))
    monkeypatch.setattr(mod, "fetch_ohlcv", lambda par, tf, limit: prep)
    monkeypatch.setattr(mod, "preparar", lambda df, estrategia: prep)
    monkeypatch.setattr(mod, "precompute_signals",
                         lambda p, estrategia: pd.Series(mod.Signal.BUY, index=p.index))
    monkeypatch.setattr(mod, "rotular",
                         lambda p, params: pd.DataFrame({"rotulo_bruto": [1.0] * len(p)}, index=p.index))
    monkeypatch.setattr(mod, "avaliar_precondicao", lambda pares, params: "baseline-fake")

    with pytest.raises(ValueError):
        mod.avaliar_precondicao_dvol(["BTC/USDT"])
