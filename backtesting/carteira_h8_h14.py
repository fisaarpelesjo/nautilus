"""H41 -- carteira combinada H8 (funding carry, delta-neutro) + H14
(direcional, classificador supervisionado). Pedido direto do operador
(2026-09-06, fora da leva H34-H40): as duas unicas hipoteses deste
registro com sinal REAL medido (nao "sem sinal", categoria distinta de
"reprovado" -- ver S6.3-b) sao H8 (+3,21%/ano liquido, delta-neutro,
`backtesting/funding_carry.py`) e H14 (z=+5,21 a +7,97, preditivo, mas
profit factor de carteira nunca passou de 0,75,
`backtesting/portfolio_h14.py`). Mecanismos DIFERENTES (custo de posicao
vs. previsao de direcao) -- ao contrario de combinar duas hipoteses
direcionais (que nao reduziria variancia de verdade, mesmo mecanismo
subjacente), esta combinacao tem motivo estrutural para diversificar.

D1: universo = UNIVERSO_H11 (12 pares) para as DUAS pernas -- mesmo
default de `simular_carteira()`/`avaliar_universo()`, evita inconsistencia
de universos diferentes por perna.

D2: alocacao 50/50 entre a perna H14 (direcional) e a perna H8 (carry)
declarada ANTES de medir -- ponto neutro, nao ajustado depois de ver o
resultado.

D3: blend sobre RETORNOS ANUALIZADOS ja calculados por cada perna
(`BacktestResult.annualized_result_pct` de H14, media pooled de
`liquido_aa_capital_implantado` dos pares validos de H8) -- NAO uma
simulacao conjunta candle-a-candle. `BacktestResult` (motor de carteira
de H14) nao expoe a curva de capital bruta fora do modulo, e H8 e por
natureza uma taxa anualizada estatica sobre uma janela historica, nao um
backtest de trade a trade. Isto e uma APROXIMACAO declarada de quanto uma
implementacao real de split de capital produziria, nao uma simulacao
completa -- limitacao relatada, nao escondida.

D4: drawdown combinado aproximado por `alocacao_h14 * drawdown_h14`
(assume a perna de carry contribui ~0 drawdown por ser delta-neutra por
construcao). Risco de base/liquidacao da perna de funding nao e
capturado neste modelo simplificado -- limitacao declarada.

D5 (criterio de aprovacao, pre-registrado 2026-09-06): diversificacao reduz
variancia, mas nao cria expectativa positiva sozinha -- H8 sozinho fica abaixo do
benchmark e H14 sozinho tem retorno economico negativo apesar do sinal
estatistico, entao um blend pode ficar menos volatil e ainda assim reprovado.
`aprovado` exige as DUAS condicoes: `retorno_combinado_aa` supera
`BENCHMARK_RENDA_FIXA_AA` (mesmo piso ja usado por H8) E
`drawdown_combinado_aproximado_pct` fica dentro de `MAX_ACCEPTABLE_DRAWDOWN_PCT`
(mesmo teto que `evaluate_approval()` ja usa para qualquer hipotese,
`backtesting/approval.py`) -- NAO comparado contra o drawdown de H14 sozinho:
sob D4 (H8 assumido ~0 drawdown), `alocacao_h14 * drawdown_h14 < drawdown_h14` e
verdadeiro por construcao para qualquer `alocacao_h14 < 1` e drawdown positivo,
o que tornaria essa condicao vazia (achado de code review, 2026-09-06) -- exigia
"reducao de risco de fato, nao so por construcao do blend" e a formula original
garantia exatamente o oposto. O teto absoluto e falsificavel; a comparacao
relativa contra a propria perna nao era. Pesos 50/50 (D2) nao sao reotimizados
apos ver o resultado -- reprovacao aqui encerra a combinacao.
"""
from dataclasses import dataclass
from typing import List, Optional

from backtesting.approval import MAX_ACCEPTABLE_DRAWDOWN_PCT
from backtesting.engine import BacktestResult
from backtesting.funding_carry import (
    BENCHMARK_RENDA_FIXA_AA,
    ResultadoFundingPar,
    avaliar_universo as avaliar_universo_h8,
)
from backtesting.horizonte import UNIVERSO_H11
from backtesting.portfolio_h14 import simular_carteira

ALOCACAO_H14 = 0.5  # D2


@dataclass
class ResultadoCombinado:
    alocacao_h14: float
    resultado_h14: BacktestResult
    resultados_h8: List[ResultadoFundingPar]
    taxa_carry_pooled_aa: float
    retorno_combinado_aa: float
    drawdown_combinado_aproximado_pct: float
    supera_benchmark: bool
    drawdown_aceitavel: bool
    aprovado: bool


def avaliar_combinado(alocacao_h14: float = ALOCACAO_H14,
                       pares: Optional[List[str]] = None) -> Optional[ResultadoCombinado]:
    """`None` quando a perna H14 nao produz resultado (universo insuficiente
    -- mesma politica de `simular_carteira`)."""
    pares = list(pares) if pares is not None else list(UNIVERSO_H11)

    resultado_h14 = simular_carteira(pares=pares)
    if resultado_h14 is None:
        return None

    resultados_h8 = avaliar_universo_h8(pares)
    taxa_carry_pooled_aa = (
        sum(r.liquido_aa_capital_implantado for r in resultados_h8) / len(resultados_h8)
        if resultados_h8 else 0.0
    )

    retorno_combinado_aa = (
        alocacao_h14 * resultado_h14.annualized_return_pct
        + (1 - alocacao_h14) * taxa_carry_pooled_aa * 100
    )
    drawdown_combinado_aproximado_pct = alocacao_h14 * resultado_h14.max_drawdown_pct

    supera_benchmark = retorno_combinado_aa > BENCHMARK_RENDA_FIXA_AA * 100
    drawdown_aceitavel = drawdown_combinado_aproximado_pct <= MAX_ACCEPTABLE_DRAWDOWN_PCT
    aprovado = supera_benchmark and drawdown_aceitavel  # D5

    return ResultadoCombinado(
        alocacao_h14=alocacao_h14, resultado_h14=resultado_h14, resultados_h8=resultados_h8,
        taxa_carry_pooled_aa=taxa_carry_pooled_aa, retorno_combinado_aa=retorno_combinado_aa,
        drawdown_combinado_aproximado_pct=drawdown_combinado_aproximado_pct,
        supera_benchmark=supera_benchmark, drawdown_aceitavel=drawdown_aceitavel, aprovado=aprovado,
    )
