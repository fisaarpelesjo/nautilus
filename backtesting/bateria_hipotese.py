"""Harness comum para a bateria E1-E6 (docs/research/registro-de-hipoteses.md
S7.1), usado pelas hipoteses H34 em diante.

Motivacao: cada hipotese anterior (H7 em cross_sectional.py, H10/H29 em
pairs_trading.py/pairs_copula.py, H12 em volatilidade.py, H14 em modelo.py...)
reimplementou por conta propria a mesma sequencia -- sanidade, janela unica,
fora da amostra, walk-forward, desconto de exposicao, sensibilidade a custo.
As pecas que ja sao genericas (`evaluate_approval`, `split_train_validation`,
`multimarket.classify`, `WalkForwardFold`, `resumir_walk_forward`,
`exposicao_de_capital`, `ganho_de_timing`) sao IMPORTADAS aqui, nao
reescritas -- a unica peca que faltava era o walk-forward generico sobre um
UNICO dataframe (o existente em cross_sectional.py e especifico de carteira
cross-sectional, `Dict[str, DataFrame]`).

Deliberadamente NAO retroage sobre H8-H33: esses modulos ja tem resultado
publicado e citado no registro, e mudar o motor deles agora arriscaria alterar
um numero ja fechado sem necessidade (mesma licao do achado M1, registro S5).
Hipoteses novas importam daqui; as antigas continuam como estao.
"""

from dataclasses import dataclass, field
from typing import Callable, List, Optional

import pandas as pd

from backtesting.approval import ApprovalVerdict, evaluate_approval
from backtesting.cross_sectional import WalkForwardFold, resumir_walk_forward
from backtesting.engine import BacktestResult
from backtesting.multimarket import classify
from backtesting.validation import (
    DEFAULT_VALIDATION_RATIO,
    MIN_WINDOW_CANDLES,
    split_train_validation,
)
from backtesting.volatilidade import exposicao_de_capital, ganho_de_timing
from utils.logger import get_logger

log = get_logger("bateria_hipotese")

# (candles, custo_zero) -> BacktestResult. `custo_zero=True` e o sinal para a
# hipotese rodar com fee/slippage zerados (E6) -- cada motor decide COMO (via
# parametro proprio), o harness so garante que os dois lados sao comparados
# com o mesmo criterio.
GerarResultado = Callable[[pd.DataFrame, bool], BacktestResult]


@dataclass
class RelatorioBateria:
    """Um campo por etapa da bateria (S7.1). `None` significa "etapa nao
    rodou" -- diferente de um veredito real, nunca deve ser lido como
    reprovacao silenciosa. Excecao: `e4_folds`/`e4_resumo` nao sao Optional
    (lista/dict vazios sao o proprio retorno de "sem folds", inclusive quando
    E1 interrompe a bateria antes de chegar em E4) -- para esses dois campos,
    use `e1_sanidade_ok` para distinguir "bateria interrompida" de "E4 rodou
    e nao produziu fold nenhum".
    """

    e1_sanidade_ok: Optional[bool] = None
    e2_janela_unica: Optional[ApprovalVerdict] = None
    e3_busca: Optional[ApprovalVerdict] = None
    e3_confirmacao: Optional[ApprovalVerdict] = None
    e3_status: Optional[str] = None  # confirmado / so_na_busca / defensivo / reprovado / inconclusivo / erro
    e4_folds: List[WalkForwardFold] = field(default_factory=list)
    e4_resumo: dict = field(default_factory=dict)
    e5_ganho_de_timing_pp: Optional[float] = None
    e6_com_custo: Optional[ApprovalVerdict] = None
    e6_sem_custo: Optional[ApprovalVerdict] = None


def walk_forward_generico(
    candles: pd.DataFrame,
    gerar_resultado: GerarResultado,
    n_janelas: int = 5,
) -> List[WalkForwardFold]:
    """Generaliza `cross_sectional.walk_forward` para qualquer hipotese de UM
    dataframe de candles (o original e especifico de carteira). Reusa o
    dataclass `WalkForwardFold` (mesmas propriedades `regime`/`passivo_pct`/
    `ganho_de_timing_pp`) para as duas formulas nao poderem divergir.
    """
    n = len(candles)
    tam = n // max(1, n_janelas)
    if tam < MIN_WINDOW_CANDLES:
        log.warning("janelas menores que MIN_WINDOW_CANDLES -- walk-forward nao aplicavel")
        return []

    folds: List[WalkForwardFold] = []
    for j in range(n_janelas):
        fatia = candles.iloc[j * tam:(j + 1) * tam]
        if fatia.empty:
            continue
        r = gerar_resultado(fatia, False)
        folds.append(WalkForwardFold(
            janela=j + 1,
            buy_hold_pct=r.buy_hold_return_pct,
            retorno_pct=r.total_return_pct,
            exposicao_pct=r.exposure_pct,
            max_drawdown_pct=r.max_drawdown_pct,
            trades=r.total_trades,
        ))
    return folds


def rodar_bateria(
    candles: pd.DataFrame,
    gerar_resultado: GerarResultado,
    *,
    teste_sanidade: Optional[Callable[[], bool]] = None,
    n_janelas_walk_forward: int = 5,
    validation_ratio: float = DEFAULT_VALIDATION_RATIO,
) -> RelatorioBateria:
    """Roda E1-E6 na ordem declarada em S7.1, sem pular etapa. Interrompe cedo
    só se E1 (sanidade) falhar -- as demais sempre rodam, mesmo se uma
    reprovar, porque o registro exige o quadro completo, não só o primeiro
    motivo de reprovação.

    `teste_sanidade` e opcional porque E1 e inerentemente especifico de cada
    hipotese (dado construido com resposta conhecida) -- o harness só garante
    que ela roda e bloqueia a bateria se falhar, para não ler defeito de motor
    como resultado de estratégia.
    """
    relatorio = RelatorioBateria()

    if teste_sanidade is not None:
        relatorio.e1_sanidade_ok = bool(teste_sanidade())
        if not relatorio.e1_sanidade_ok:
            return relatorio

    resultado_completo = gerar_resultado(candles, False)
    relatorio.e2_janela_unica = evaluate_approval(resultado_completo)

    busca_df, confirmacao_df = split_train_validation(candles, validation_ratio=validation_ratio)
    # Historico curto demais para dividir: split_train_validation devolve o
    # dataframe inteiro como busca_df (inconclusivo) -- reusa resultado_completo
    # em vez de rodar a mesma simulacao duas vezes.
    resultado_busca = resultado_completo if confirmacao_df is None else gerar_resultado(busca_df, False)
    resultado_confirmacao = gerar_resultado(confirmacao_df, False) if confirmacao_df is not None else None
    relatorio.e3_busca = evaluate_approval(resultado_busca)
    relatorio.e3_confirmacao = (
        evaluate_approval(resultado_confirmacao) if resultado_confirmacao is not None else None
    )
    relatorio.e3_status = classify(resultado_busca, resultado_confirmacao)

    relatorio.e4_folds = walk_forward_generico(candles, gerar_resultado, n_janelas=n_janelas_walk_forward)
    relatorio.e4_resumo = resumir_walk_forward(relatorio.e4_folds)

    relatorio.e5_ganho_de_timing_pp = ganho_de_timing(
        resultado_completo, exposicao_de_capital(resultado_completo)
    )

    relatorio.e6_com_custo = relatorio.e2_janela_unica
    resultado_sem_custo = gerar_resultado(candles, True)
    relatorio.e6_sem_custo = evaluate_approval(resultado_sem_custo)

    return relatorio
