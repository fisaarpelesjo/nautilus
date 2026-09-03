"""Perfis de geometria e regra de seleção (spec 028, H20)."""
import pytest

from backtesting.geometria import (
    ELEVACAO_H14,
    FOLGA,
    MIN_DESFECHOS,
    SL_FIXO,
    TETO_PCT_TEMPO,
    TPS_CANDIDATOS,
    PerfilGeometria,
    medir_perfis,
    regra_declarada,
    run_geometria_scan,
    selecionar,
)


def _perfil(tp, alvo, stop, tempo=0):
    return PerfilGeometria(tp_mult=tp, n_alvo=alvo, n_stop=stop, n_tempo=tempo)


# ------------------------------------------------------------ grandezas (US1)

def test_empate_e_stop_sobre_alvo():
    assert _perfil(3.0, 100, 100).empate == pytest.approx(0.5)
    assert _perfil(2.0, 100, 100).empate == pytest.approx(0.75)
    assert _perfil(6.0, 100, 100).empate == pytest.approx(0.25)


def test_limite_de_tempo_nao_conta_como_desfecho():
    """FR-009 — a razão de chances descreve apenas eventos que tocam alvo ou
    stop. Contar o limite de tempo como desfecho a diluiria."""
    p = _perfil(3.0, alvo=300, stop=700, tempo=500)

    assert p.n_desfechos == 1000
    assert p.n_total == 1500
    assert p.pct_tempo == pytest.approx(500 / 1500 * 100)
    assert p.razao_base == pytest.approx(300 / 700)


def test_razao_sem_stop_e_infinita_nao_zero():
    assert _perfil(3.0, alvo=10, stop=0).razao_base == float("inf")


def test_razao_sem_amostra_e_none():
    assert _perfil(3.0, alvo=0, stop=0).razao_base is None


# ============================================ a regra de seleção (US2, FR-003)

def test_regra_exibida_e_a_regra_aplicada():
    """FR-003 — o texto do relatório não pode divergir do código. Se os números
    da regra mudarem, o texto muda junto, porque sai das mesmas constantes."""
    texto = regra_declarada()

    assert str(ELEVACAO_H14) in texto
    assert str(FOLGA) in texto
    assert str(MIN_DESFECHOS) in texto
    assert f"{TETO_PCT_TEMPO:.0f}" in texto


def test_criterio_de_margem_usa_elevacao_e_folga():
    # razao x 1,318 >= empate x 1,09. Em tp=2,0 o empate e 0,750, entao a razao
    # precisa de pelo menos 0,750 x 1,09 / 1,318 = 0,6202.
    limite = 0.75 * FOLGA / ELEVACAO_H14

    apertado = _perfil(2.0, alvo=int(1000 * limite * 1.01), stop=1000)
    frouxo = _perfil(2.0, alvo=int(1000 * limite * 0.99), stop=1000)

    assert "c1 margem" not in apertado.motivos_inelegibilidade
    assert "c1 margem" in frouxo.motivos_inelegibilidade


def test_excesso_de_limite_de_tempo_torna_inelegivel():
    p = _perfil(2.0, alvo=800, stop=1000, tempo=2000)

    assert p.pct_tempo > TETO_PCT_TEMPO
    assert "c2 limite de tempo" in p.motivos_inelegibilidade


def test_amostra_pequena_torna_inelegivel():
    p = _perfil(2.0, alvo=80, stop=100)

    assert p.n_desfechos < MIN_DESFECHOS
    assert "c3 amostra" in p.motivos_inelegibilidade


def test_seleciona_a_de_menor_tp_e_nao_a_de_maior_margem():
    """A regra escolhe a mais conservadora, não a melhor.

    Maximizar a margem seria otimizar sobre o conjunto e reintroduziria o
    problema de testes múltiplos por outra porta — que é exatamente o risco que
    define esta spec.
    """
    # tp=4,0 tem margem folgada; tp=2,0 passa raspando. A regra pega tp=2,0.
    apertada = _perfil(2.0, alvo=630, stop=1000)          # razao 0,630
    folgada = _perfil(4.0, alvo=900, stop=1000)           # razao 0,900

    assert apertada.elegivel and folgada.elegivel
    assert folgada.razao_base > apertada.razao_base
    assert selecionar([folgada, apertada]).tp_mult == 2.0


def test_selecao_e_deterministica():
    """FR-005 — mesmas entradas, mesma geometria, independente da ordem."""
    a = _perfil(2.0, alvo=630, stop=1000)
    b = _perfil(4.0, alvo=900, stop=1000)

    assert selecionar([a, b]).tp_mult == selecionar([b, a]).tp_mult


def test_nenhuma_elegivel_devolve_none_e_nao_relaxa():
    """FR-006 — desfecho legítimo, não erro. A regra não é afrouxada para
    produzir uma candidata."""
    perfis = [_perfil(tp, alvo=50, stop=1000) for tp in TPS_CANDIDATOS]

    assert all(not p.elegivel for p in perfis)
    assert selecionar(perfis) is None


def test_perfil_com_erro_e_inelegivel():
    p = _perfil(2.0, alvo=900, stop=1000)
    p.erro = "nenhum evento rotulavel"

    assert not p.elegivel


# ------------------------------ a regra NÃO consulta desempenho (FR-004)

def test_selecao_nao_importa_nada_de_modelo():
    """FR-004 — a regra só pode usar propriedades da série e a elevação medida
    em H14. Importar o módulo de modelo abriria a porta para consultar
    desempenho da geometria candidata, que é o que transforma isto em varredura.
    """
    import ast
    from pathlib import Path

    arvore = ast.parse(Path("backtesting/geometria.py").read_text(encoding="utf-8"))
    importados = set()
    for no in ast.walk(arvore):
        if isinstance(no, ast.Import):
            importados.update(a.name for a in no.names)
        elif isinstance(no, ast.ImportFrom) and no.module:
            importados.add(no.module)

    assert not any("modelo" in m for m in importados), importados


def test_constantes_da_regra_sao_as_declaradas_em_d1():
    """As constantes foram commitadas em 7cc19e0, antes de qualquer medição.
    Alterá-las depois invalidaria a procedência — este teste torna a alteração
    visível."""
    assert ELEVACAO_H14 == 1.318
    assert FOLGA == 1.09
    assert TETO_PCT_TEMPO == 25.0
    assert MIN_DESFECHOS == 1000
    assert SL_FIXO == 1.5
    assert TPS_CANDIDATOS == (2.0, 2.5, 3.0, 4.0, 5.0, 6.0)


# ------------------------------------------- medição sobre série sintética

def _serie(n=400, semente=3):
    import numpy as np
    import pandas as pd

    from backtesting.horizonte import preparar
    from strategy.ema_rsi import EmaRsiStrategy

    rng = np.random.default_rng(semente)
    p = 100 * np.exp(np.cumsum(rng.normal(0.0004, 0.01, n)))
    df = pd.DataFrame({
        "open": p, "close": p, "high": p * 1.01, "low": p * 0.99,
        "volume": rng.uniform(1e4, 1e6, n),
    }, index=pd.date_range("2026-01-01", periods=n, freq="4h"))
    return preparar(df, EmaRsiStrategy())


def test_medicao_cobre_todas_as_candidatas():
    perfis = medir_perfis({"X/USDT": _serie()})

    assert [p.tp_mult for p in perfis] == list(TPS_CANDIDATOS)
    assert all(p.n_total > 0 for p in perfis)


# ==================================== spec 048 (historico estendido)

def test_run_geometria_scan_pede_6000_candles(monkeypatch):
    """D1, specs/048-h20-historico-estendido/research.md -- mesmo teto ja
    aplicado a modelo.py/onchain_hipotese.py/horizonte.py por spec 036."""
    import numpy as np
    import pandas as pd

    chamadas = []

    def _fake_fetch(par, timeframe, limit):
        chamadas.append(limit)
        rng = np.random.default_rng(3)
        p = 100 * np.exp(np.cumsum(rng.normal(0.0004, 0.01, 400)))
        return pd.DataFrame({
            "open": p, "close": p, "high": p * 1.01, "low": p * 0.99,
            "volume": rng.uniform(1e4, 1e6, 400),
        }, index=pd.date_range("2026-01-01", periods=400, freq="4h"))

    # run_geometria_scan importa fetch_ohlcv localmente (`from data.fetcher
    # import fetch_ohlcv` dentro da funcao) -- monkeypatch no modulo de origem.
    import data.fetcher as fetcher_mod
    monkeypatch.setattr(fetcher_mod, "fetch_ohlcv", _fake_fetch)

    run_geometria_scan(pares=["X/USDT"])

    assert chamadas == [6000]


def test_alvo_mais_distante_reduz_a_razao_de_chances():
    """A propriedade que refutou a tese de H20: afastar o alvo derruba a razão
    de chances. Se ela caísse mais devagar que o ponto de empate, a geometria
    seria uma alavanca — os dados dizem o contrário."""
    perfis = {p.tp_mult: p for p in medir_perfis({"X/USDT": _serie(n=800)})}

    razoes = [perfis[tp].razao_base for tp in (2.0, 3.0, 4.0, 6.0)]

    # Pares consecutivos: cada geometria tem razao maior ou igual a seguinte.
    consecutivos = [(razoes[i], razoes[i + 1]) for i in range(len(razoes) - 1)]
    assert all(a >= b for a, b in consecutivos), razoes
