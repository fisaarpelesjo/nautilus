import math

import pytest

from backtesting import volatilidade as V
from backtesting.volatilidade import ParametrosVolatilidade, fator_volatilidade


# ------------------------------------------------------------ T002 fumaca

def test_modulo_expoe_a_api_publica():
    for nome in ("ParametrosVolatilidade", "fator_volatilidade",
                 "ComparacaoPareada", "comparar_combinacao",
                 "run_volatilidade_scan"):
        assert hasattr(V, nome), f"{nome} ausente"


# --------------------------------------------- T003 teto, o invariante central

@pytest.mark.parametrize("atr_ratio", [1e-9, 1e-6, 0.001, 0.005, 0.0187, 0.05, 0.5])
def test_fator_nunca_excede_um(atr_ratio):
    """FR-003 + constituição (max_leverage=1).

    O `min(1.0, ...)` é a fórmula, não validação defensiva: não pode existir
    caminho pelo qual esta feature amplie exposição.
    """
    assert fator_volatilidade(atr_ratio) <= 1.0


@pytest.mark.parametrize("alvo", [0.02, 0.1, 0.5, 10.0])
def test_fator_nao_excede_um_nem_com_alvo_absurdo(alvo):
    """Cenário 4 do quickstart: alvo muito acima de qualquer atr_ratio real
    (p99 medido = 0,0474) deve saturar em 1,0, não ampliar."""
    p = ParametrosVolatilidade(alvo=alvo)

    for atr_ratio in (0.0001, 0.0064, 0.0187, 0.0474):
        assert fator_volatilidade(atr_ratio, p) <= 1.0


def test_alvo_muito_alto_produz_fator_exatamente_um():
    p = ParametrosVolatilidade(alvo=0.5)

    assert fator_volatilidade(0.0187, p) == 1.0


# --------------------------------------- T004 dado invalido recai no vigente

@pytest.mark.parametrize("invalido", [
    None, 0.0, -0.01, float("nan"), float("inf"), float("-inf"),
])
def test_atr_ratio_invalido_devolve_fator_um(invalido):
    """FR-012 — dado desconhecido não vira decisão silenciosa.

    Recair no tamanho vigente é a política de falha do projeto. Divisão por zero
    ou posição infinita seriam as alternativas.
    """
    assert fator_volatilidade(invalido) == 1.0


def test_atr_ratio_invalido_nao_levanta_excecao():
    for invalido in (None, 0.0, float("nan")):
        fator_volatilidade(invalido)


# ------------------------------------------------ T005 monotonicidade

def test_fator_decresce_quando_a_volatilidade_sobe():
    p = ParametrosVolatilidade(alvo=0.02, fator_minimo=0.0)
    valores = [fator_volatilidade(v, p) for v in (0.02, 0.04, 0.08, 0.16)]

    assert valores == sorted(valores, reverse=True)
    assert valores[0] > valores[-1]


def test_dobrar_a_volatilidade_reduz_o_fator_a_metade():
    p = ParametrosVolatilidade(alvo=0.02, fator_minimo=0.0)

    assert fator_volatilidade(0.04, p) == pytest.approx(0.5)
    assert fator_volatilidade(0.08, p) == pytest.approx(0.25)


def test_volatilidade_no_alvo_produz_fator_um():
    p = ParametrosVolatilidade(alvo=0.02)

    assert fator_volatilidade(0.02, p) == pytest.approx(1.0)


# ------------------------------------------------------- T006 piso do fator

def test_fator_respeita_o_piso():
    """Volatilidade extrema não pode produzir posição que a corretora recusa."""
    p = ParametrosVolatilidade(alvo=0.02, fator_minimo=0.25)

    assert fator_volatilidade(10.0, p) == pytest.approx(0.25)


def test_piso_nao_eleva_fator_de_volatilidade_moderada():
    p = ParametrosVolatilidade(alvo=0.02, fator_minimo=0.25)

    assert fator_volatilidade(0.04, p) == pytest.approx(0.5)


def test_fator_fica_entre_piso_e_um_para_qualquer_entrada():
    p = ParametrosVolatilidade(alvo=0.02, fator_minimo=0.2)

    for v in (1e-9, 0.001, 0.0187, 0.05, 0.5, 5.0, 1e6):
        f = fator_volatilidade(v, p)
        assert p.fator_minimo <= f <= 1.0
        assert math.isfinite(f)


# ======================================== T009 T010 — guardas de integracao

def _serie(n=400, semente=2):
    import numpy as np
    import pandas as pd
    rng = np.random.default_rng(semente)
    preco = 100 * np.exp(np.cumsum(rng.normal(0.0004, 0.02, n)))
    idx = pd.date_range("2024-01-01", periods=n, freq="1D")
    return pd.DataFrame({
        "open": preco, "close": preco, "high": preco * 1.02,
        "low": preco * 0.98, "volume": np.full(n, 1000.0),
    }, index=idx)


def test_default_do_motor_nao_altera_nada():
    """T009 — o parâmetro é opcional e seu default reproduz o comportamento
    vigente. Sem esta garantia, adicionar a feature mudaria silenciosamente todo
    resultado histórico já registrado."""
    from backtesting.engine import simulate_backtest
    from backtesting.horizonte import preparar
    from strategy.ema_rsi import EmaRsiStrategy

    e = EmaRsiStrategy()
    df = preparar(_serie(), e)

    sem_param = simulate_backtest(df, e, start_index=50)
    com_none = simulate_backtest(df, e, start_index=50, position_sizer=None)

    assert sem_param.total_trades == com_none.total_trades
    assert sem_param.total_return_pct == pytest.approx(com_none.total_return_pct)
    assert sem_param.max_drawdown_pct == pytest.approx(com_none.max_drawdown_pct)
    assert sem_param.final_capital == pytest.approx(com_none.final_capital)


def test_sizer_que_devolve_um_equivale_a_nao_passar_sizer():
    """Fator 1,0 em toda vela: o resultado tem de ser idêntico à linha de base.
    É o cenário 4 do quickstart em forma de teste unitário."""
    from backtesting.engine import simulate_backtest
    from backtesting.horizonte import preparar
    from strategy.ema_rsi import EmaRsiStrategy

    e = EmaRsiStrategy()
    df = preparar(_serie(), e)

    base = simulate_backtest(df, e, start_index=50)
    neutro = simulate_backtest(df, e, start_index=50, position_sizer=lambda linha: 1.0)

    assert base.total_trades == neutro.total_trades
    assert base.final_capital == pytest.approx(neutro.final_capital)


def test_sizer_reduz_a_exposicao_e_o_capital_movimentado():
    """Fator constante < 1 tem de reduzir o tamanho, não o número de sinais:
    o dimensionamento decide QUANTO, nunca SE (FR-002)."""
    from backtesting.engine import simulate_backtest
    from backtesting.horizonte import preparar
    from strategy.ema_rsi import EmaRsiStrategy

    e = EmaRsiStrategy()
    df = preparar(_serie(), e)

    base = simulate_backtest(df, e, start_index=50)
    meio = simulate_backtest(df, e, start_index=50, position_sizer=lambda linha: 0.5)

    assert base.total_trades == meio.total_trades, "o sizer nao pode alterar o sinal"
    if base.total_trades > 0:
        assert abs(meio.total_return_pct) <= abs(base.total_return_pct) + 1e-9


def test_modulo_nao_depende_de_risk_manager():
    """T010 / FR-013 — guarda contra regressão de escopo.

    `risk/manager.py` é caminho de produção, sujeito ao princípio Safety First da
    constituição. Esta feature não pode alcançá-lo nem por importação indireta.
    """
    import ast
    from pathlib import Path

    # Checagem sobre as IMPORTACOES, nao sobre o texto do arquivo: o docstring do
    # modulo menciona `risk/manager.py` justamente para declarar que nao o toca,
    # e uma busca por string acusaria essa mencao como violacao.
    arvore = ast.parse(Path("backtesting/volatilidade.py").read_text(encoding="utf-8"))
    importados = set()
    for no in ast.walk(arvore):
        if isinstance(no, ast.Import):
            importados.update(a.name for a in no.names)
        elif isinstance(no, ast.ImportFrom) and no.module:
            importados.add(no.module)

    assert not any(m.startswith("risk") for m in importados), importados


def test_sizer_recebe_a_linha_do_candle_e_consegue_ler_atr_ratio():
    """Contrato do sizer: recebe a linha corrente, com os indicadores já
    calculados. É o que permite usar `atr_ratio` sem recomputar nada."""
    from backtesting.engine import simulate_backtest
    from backtesting.horizonte import preparar
    from strategy.ema_rsi import EmaRsiStrategy

    e = EmaRsiStrategy()
    df = preparar(_serie(), e)
    vistos = []

    def sizer(linha):
        vistos.append(linha.get("atr_ratio"))
        return 1.0

    simulate_backtest(df, e, start_index=50, position_sizer=sizer)

    if vistos:
        assert all(v is not None for v in vistos)
