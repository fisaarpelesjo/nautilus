"""Purga e embargo na divisão treino/teste (spec 027, H14, US2)."""
import pandas as pd
import pytest

from backtesting.purga import DivisaoPurgada, dividir_com_purga


def _eventos(n=100, par="BTC/USDT", horizonte=3, inicio="2026-01-01"):
    """Eventos regulares em que o horizonte de cada um alcança `horizonte`
    velas à frente."""
    idx = pd.date_range(inicio, periods=n, freq="4h")
    fim = [idx[min(i + horizonte, n - 1)] for i in range(n)]
    return pd.DataFrame({
        "instante": idx,
        "par": [par] * n,
        "rotulo": [i % 2 for i in range(n)],
        "fim_horizonte": fim,
    })


# ------------------------------------------------ T009 purga por sobreposição

def test_nenhuma_amostra_de_treino_alcanca_a_janela_de_teste():
    """FR-005 — o rótulo em `t` só é conhecido em `fim_horizonte`. Treinar com
    amostras cujo desfecho só se conhece dentro do teste entrega futuro ao
    modelo. É o análogo, em aprendizado supervisionado, do achado M2."""
    ev = _eventos(n=100, horizonte=5)

    d = dividir_com_purga(ev, ratio_teste=0.3, embargo_velas=0)

    treino = ev.loc[d.indices_treino]
    assert len(treino) > 0
    assert (treino["fim_horizonte"] < d.inicio_teste).all()


def test_purga_conta_quantas_removeu():
    ev = _eventos(n=100, horizonte=5)

    d = dividir_com_purga(ev, ratio_teste=0.3, embargo_velas=0)

    assert d.n_purgadas > 0
    assert d.n_purgadas <= 5


def test_horizonte_zero_nao_purga_nada():
    ev = _eventos(n=100, horizonte=0)

    d = dividir_com_purga(ev, ratio_teste=0.3, embargo_velas=0)

    assert d.n_purgadas == 0


# ---------------------------------------------------------------- T010 embargo

def test_embargo_remove_amostras_apos_o_teste():
    """FR-006 — o embargo protege contra a cauda do horizonte, não contra a
    mediana. Sem ele, amostras logo após o teste ainda carregam informação
    correlacionada com ele."""
    ev = _eventos(n=200, horizonte=2)

    sem = dividir_com_purga(ev, ratio_teste=0.3, embargo_velas=0)
    com = dividir_com_purga(ev, ratio_teste=0.3, embargo_velas=10)

    assert com.n_embargadas > 0
    assert len(com.indices_treino) < len(sem.indices_treino)


def test_embargo_zero_nao_remove_nada():
    ev = _eventos(n=200, horizonte=2)

    assert dividir_com_purga(ev, ratio_teste=0.3, embargo_velas=0).n_embargadas == 0


# ================================================= T011 A PURGA E GLOBAL (D4)

def test_purga_e_global_entre_pares():
    """D4 — o defeito que a correlação de 0,71 tornaria invisível.

    Criptoativos se movem juntos (medido em H9). Se a purga fosse aplicada par a
    par, a amostra de BTC no instante `t` permaneceria no treino enquanto a de
    ETH em `t` estivesse no teste — e o modelo veria, pelo BTC, o desfecho que
    deveria prever para o ETH.
    """
    btc = _eventos(n=100, par="BTC/USDT", horizonte=5)
    eth = _eventos(n=100, par="ETH/USDT", horizonte=5)
    ev = pd.concat([btc, eth], ignore_index=True)

    d = dividir_com_purga(ev, ratio_teste=0.3, embargo_velas=0)

    treino = ev.loc[d.indices_treino]
    # Nenhuma amostra, de QUALQUER par, alcanca a janela de teste.
    assert (treino["fim_horizonte"] < d.inicio_teste).all()
    # E a purga atingiu os dois pares, nao so um.
    purgados = ev.loc[~ev.index.isin(d.indices_treino) & (ev["instante"] < d.inicio_teste)]
    assert set(purgados["par"]) == {"BTC/USDT", "ETH/USDT"}


def test_a_fronteira_de_teste_e_temporal_nao_posicional():
    """Com pares agrupados, cortar por posição na lista misturaria instantes.
    A fronteira tem de ser um instante do calendário."""
    btc = _eventos(n=100, par="BTC/USDT", horizonte=1)
    eth = _eventos(n=100, par="ETH/USDT", horizonte=1)
    ev = pd.concat([btc, eth], ignore_index=True)

    d = dividir_com_purga(ev, ratio_teste=0.3, embargo_velas=0)

    teste = ev.loc[d.indices_teste]
    assert (teste["instante"] >= d.inicio_teste).all()
    assert set(teste["par"]) == {"BTC/USDT", "ETH/USDT"}


# ---------------------------------------------------- T012 treino esvaziado

def test_purga_que_esvazia_o_treino_e_sinalizada():
    """FR-005/FR-011 — amostra insuficiente é inconclusiva, nunca reprovação."""
    ev = _eventos(n=20, horizonte=50)  # horizonte maior que a serie

    d = dividir_com_purga(ev, ratio_teste=0.3, embargo_velas=0)

    assert len(d.indices_treino) == 0
    assert d.suficiente(minimo=10) is False


def test_treino_amplo_e_suficiente():
    d = dividir_com_purga(_eventos(n=1000, horizonte=3), ratio_teste=0.3, embargo_velas=5)

    assert d.suficiente(minimo=10) is True


def test_eventos_vazios_sao_recusados():
    with pytest.raises(ValueError, match="vazio"):
        dividir_com_purga(_eventos(n=0), ratio_teste=0.3, embargo_velas=0)


def test_ratio_invalido_e_recusado():
    for ratio in (0.0, 1.0, -0.1, 1.5):
        with pytest.raises(ValueError, match="ratio"):
            dividir_com_purga(_eventos(n=100), ratio_teste=ratio, embargo_velas=0)


def test_divisao_expoe_os_campos_do_relatorio():
    d = dividir_com_purga(_eventos(n=500, horizonte=3), ratio_teste=0.3, embargo_velas=5)

    assert isinstance(d, DivisaoPurgada)
    for campo in ("inicio_teste", "fim_teste", "n_purgadas", "n_embargadas",
                  "embargo_velas"):
        assert getattr(d, campo) is not None
