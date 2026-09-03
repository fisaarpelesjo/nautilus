"""H8 -- arbitragem de funding rate (delta-neutro): revisao com universo
mais amplo, taxas atuais (VIP0, verificadas 2026-09-03) e eficiencia de
capital corrigida. `specs/058-h8-funding-rate-revisao/research.md` declara
os cinco pontos (D1-D5) antes de qualquer medicao:

D1 (taxas atuais): spot taker 0,10% (`BACKTEST_FEE_RATE`, ja verificado
para H20), futures taker 0,05% (VIP0, verificado via busca 2026-09-03) --
a medicao original de H8 usava 0,04% para as duas pernas, subestimando o
lado spot.

D2 (custo de abertura/fechamento): evento UNICO por posicao mantida
(abre spot + abre perp no inicio, fecha os dois no fim) -- nao um custo
recorrente. Anualizado na MESMA base que o bruto (`fator_anual`) para os
dois ficarem comparaveis, o que pesa proporcionalmente mais quando o
historico disponivel e menor que um ano.

D3 (eficiencia de capital -- a correcao central desta revisao): a
medicao original reportou retorno sobre o NOCIONAL. Uma posicao
delta-neutra SEM ALAVANCAGEM (a unica configuracao que praticamente
elimina risco de liquidacao, ja que a margem cobre o nocional inteiro)
exige capital = nocional (perna spot) + margem (perna perpetua, ~=
nocional a 1x) = 2x o nocional. O retorno real sobre capital IMPLANTADO
e, portanto, aproximadamente METADE do retorno sobre nocional.

D4 (benchmark de custo de oportunidade): 5% a.a., piso conservador da
faixa 5-8% observada em produtos de emprestimo de USDT em plataformas
estabelecidas (Binance Earn, Aave, verificado via busca 2026-09-03) --
nao um numero arbitrario.

D5 (universo): `UNIVERSO_AMPLO` (`backtesting/portfolio_h14.py`, 34
pares, ja filtrado por liquidez de spot para outra pesquisa, nao
escolhido para este teste) intersectado com pares que tem mercado
perpetuo ativo E pelo menos 90 dias de historico de funding -- piso de
qualidade de dado, nao um filtro de resultado.
"""
from dataclasses import dataclass
from typing import List, Optional

from config.settings import BACKTEST_FEE_RATE
from data.funding import fetch_funding_rate_history

FUTURES_TAKER_FEE = 0.0005  # VIP0, verificado 2026-09-03 (D1)
CUSTO_ABERTURA_FECHAMENTO = 2 * (BACKTEST_FEE_RATE + FUTURES_TAKER_FEE)  # 4 pernas, evento unico
BENCHMARK_RENDA_FIXA_AA = 0.05  # piso conservador, 5-8% observado (D4)
MIN_DIAS_COBERTURA = 90  # piso de qualidade de dado (D5)


@dataclass
class ResultadoFundingPar:
    par: str
    dias_cobertos: int
    n_pagamentos: int
    pct_negativos: float
    bruto_aa: float
    liquido_aa_nocional: float
    liquido_aa_capital_implantado: float
    supera_benchmark: bool


def avaliar_par(par: str, dias: int = 365) -> Optional[ResultadoFundingPar]:
    """`None` quando o par nao tem mercado perpetuo, ou tem menos que
    `MIN_DIAS_COBERTURA` dias de historico -- excluido do universo, nunca
    contado como zero silencioso."""
    hist = fetch_funding_rate_history(par, dias=dias)
    if len(hist) == 0:
        return None

    dias_cobertos = (hist.index[-1] - hist.index[0]).days
    if dias_cobertos < MIN_DIAS_COBERTURA:
        return None

    n = len(hist)
    pct_negativos = float((hist["fundingRate"] < 0).mean() * 100)
    soma = float(hist["fundingRate"].sum())

    fator_anual = 365.0 / dias_cobertos
    bruto_aa = soma * fator_anual
    liquido_aa_nocional = bruto_aa - CUSTO_ABERTURA_FECHAMENTO * fator_anual
    liquido_aa_capital_implantado = liquido_aa_nocional / 2.0

    return ResultadoFundingPar(
        par=par, dias_cobertos=dias_cobertos, n_pagamentos=n,
        pct_negativos=pct_negativos, bruto_aa=bruto_aa,
        liquido_aa_nocional=liquido_aa_nocional,
        liquido_aa_capital_implantado=liquido_aa_capital_implantado,
        supera_benchmark=liquido_aa_capital_implantado > BENCHMARK_RENDA_FIXA_AA,
    )


def avaliar_universo(pares: List[str], dias: int = 365) -> List[ResultadoFundingPar]:
    resultados = []
    for par in pares:
        r = avaliar_par(par, dias=dias)
        if r is not None:
            resultados.append(r)
    return resultados
