"""H25 -- sazonalidade por sessao de negociacao, hora do dia (spec 062)."""
import pandas as pd

from backtesting.engine import Signal
from backtesting.sazonalidade import filtrar_por_sessao


def _idx(n, freq="4h"):
    return pd.date_range("2026-01-01", periods=n, freq=freq)


def test_filtrar_por_sessao_bloqueia_buy_fora_da_janela():
    idx = _idx(6)  # horas 0,4,8,12,16,20
    sinais = pd.Series([Signal.BUY] * 6, index=idx)

    r = filtrar_por_sessao(sinais, 8, 16)

    assert list(r) == [Signal.HOLD, Signal.HOLD, Signal.BUY, Signal.BUY, Signal.HOLD, Signal.HOLD]


def test_filtrar_por_sessao_nunca_bloqueia_sell():
    idx = _idx(6)
    sinais = pd.Series([Signal.SELL] * 6, index=idx)

    r = filtrar_por_sessao(sinais, 8, 16)

    assert list(r) == [Signal.SELL] * 6  # sinal de venda nunca e tocado


def test_filtrar_por_sessao_preserva_hold_original():
    idx = _idx(3)
    sinais = pd.Series([Signal.HOLD, Signal.BUY, Signal.SELL], index=idx)  # horas 0,4,8

    r = filtrar_por_sessao(sinais, 8, 16)

    assert list(r) == [Signal.HOLD, Signal.HOLD, Signal.SELL]  # BUY as 4h bloqueado, SELL as 8h preservado


def test_filtrar_por_sessao_janela_asia_permite_madrugada_utc():
    idx = _idx(2)  # horas 0, 4
    sinais = pd.Series([Signal.BUY, Signal.BUY], index=idx)

    r = filtrar_por_sessao(sinais, 0, 8)

    assert list(r) == [Signal.BUY, Signal.BUY]


def test_avaliar_par_janela_erro_de_busca_nao_quebra_e_marca_status_erro(monkeypatch):
    from backtesting import sazonalidade

    def _explode(par, timeframe, limit=2000):
        raise RuntimeError("falha de rede simulada")

    monkeypatch.setattr(sazonalidade, "fetch_ohlcv", _explode)

    r = sazonalidade._avaliar_par_janela("BTC/USDT", "asia", 0, 8)

    assert r.status == "erro"
    assert r.erro is not None
    assert r.pf_busca_base is None


def test_avaliar_sazonalidade_continua_apos_um_par_com_erro(monkeypatch):
    from backtesting import sazonalidade

    def _fake_avaliar(par, janela_nome, inicio, fim, candle_limit=2000, initial_capital=1000.0):
        if par == "RUIM/USDT":
            return sazonalidade.ResultadoSazonalidadePar(
                par=par, janela_nome=janela_nome, pf_busca_base=None,
                pf_busca_filtrado=None, status="erro", erro="falhou",
            )
        return sazonalidade.ResultadoSazonalidadePar(
            par=par, janela_nome=janela_nome, pf_busca_base=1.0,
            pf_busca_filtrado=1.0, status="reprovado",
        )

    monkeypatch.setattr(sazonalidade, "_avaliar_par_janela", _fake_avaliar)

    resultados = sazonalidade.avaliar_sazonalidade(
        pares=["RUIM/USDT", "BOM/USDT"], janelas={"asia": (0, 8)},
    )

    assert len(resultados) == 2
    status_por_par = {r.par: r.status for r in resultados}
    assert status_por_par["RUIM/USDT"] == "erro"
    assert status_por_par["BOM/USDT"] == "reprovado"


def test_janelas_cobrem_as_24_horas_sem_sobreposicao():
    from backtesting.sazonalidade import JANELAS

    horas_cobertas = set()
    for inicio, fim in JANELAS.values():
        for h in range(inicio, fim):
            assert h not in horas_cobertas, f"hora {h} coberta por mais de uma janela"
            horas_cobertas.add(h)

    assert horas_cobertas == set(range(24))
