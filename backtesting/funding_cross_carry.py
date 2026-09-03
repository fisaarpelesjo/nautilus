"""H24 -- diferencial de funding rate entre corretoras (perp x perp, sem
perna a vista). `specs/061-h24-funding-cross-exchange/research.md`
declara antes de medir:

D1 (corretoras qualificadas): binance/bybit/okx/kucoinfutures/gate --
verificado por chamada real 2026-09-03. Kraken excluido (so oferece
perpetuo inverso USD/BTC-margined, nao linear USDT-margined).

D2 (custo real por corretora): cada corretora tem sua propria taxa de
tomador (`data/funding_cross.py::TAXA_TOMADOR`, verificada por busca)
-- custo do par = 2*(taxa_A + taxa_B), evento unico anualizado na mesma
base do bruto (mesmo padrao de H8/H23).

D3 (eficiencia de capital -- achado central, NAO presumido): investigado
e declarado que a exigencia de capital de H24 e IGUAL a H8 (2x o
nocional, margem propria por perna, sem margem cruzada entre
corretoras), com risco adicional de capital pre-posicionado em duas
corretoras. A hipotese de entrada (mais eficiente que H8) foi refutada
antes de qualquer medicao de diferencial.

D4/D5 (universo e benchmark): BTC/USDT e ETH/USDT, mesmo benchmark de
5% a.a. de `backtesting/funding_carry.py::BENCHMARK_RENDA_FIXA_AA`,
reusado sem alteracao.
"""
from dataclasses import dataclass
from itertools import combinations
from typing import List, Optional, Sequence

import pandas as pd

from backtesting.funding_carry import BENCHMARK_RENDA_FIXA_AA
from data.funding_cross import (
    CORRETORAS_QUALIFICADAS,
    TAXA_TOMADOR,
    fetch_funding_rate_history,
)

MIN_DIAS_COBERTURA = 90  # mesmo piso de qualidade de dado de H8
# Buffer sobre o piso: pedir exatamente `dias=90` produz cobertura real de
# ~89 dias (a janela `desde = ate - dias*ms` nao alinha perfeitamente com o
# primeiro/ultimo periodo de funding dentro dela) -- sem a folga, o piso
# nunca e alcancavel. Achado real medido, nao suposicao.
DIAS_PADRAO = 95


@dataclass
class ResultadoDiferencialCorretoras:
    corretora_a: str
    corretora_b: str
    par: str
    dias_cobertos: int
    n_periodos: int
    diferencial_bruto_aa: float
    diferencial_liquido_aa_nocional: float
    diferencial_liquido_aa_capital_implantado: float
    direcao: str
    supera_benchmark: bool


def _alinhar_por_hora(hist_a: pd.DataFrame, hist_b: pd.DataFrame) -> pd.DataFrame:
    """Alinha dois historicos de funding por hora arredondada -- absorve
    o jitter de poucos segundos observado em algumas corretoras (D1)."""
    a = hist_a.copy()
    b = hist_b.copy()
    a.index = a.index.round("h")
    b.index = b.index.round("h")
    a = a[~a.index.duplicated(keep="last")]
    b = b[~b.index.duplicated(keep="last")]
    return a.join(b, how="inner", lsuffix="_a", rsuffix="_b")


def avaliar_par_corretoras(corretora_a: str, corretora_b: str, par: str,
                            dias: int = DIAS_PADRAO) -> Optional[ResultadoDiferencialCorretoras]:
    """`None` quando alguma corretora nao tem o par, ou a interseccao
    alinhada tem menos que `MIN_DIAS_COBERTURA` dias."""
    hist_a = fetch_funding_rate_history(corretora_a, par, dias=dias)
    hist_b = fetch_funding_rate_history(corretora_b, par, dias=dias)
    if len(hist_a) == 0 or len(hist_b) == 0:
        return None

    alinhado = _alinhar_por_hora(hist_a, hist_b)
    if len(alinhado) == 0:
        return None

    dias_cobertos = (alinhado.index[-1] - alinhado.index[0]).days
    if dias_cobertos < MIN_DIAS_COBERTURA:
        return None

    diff = alinhado["fundingRate_a"] - alinhado["fundingRate_b"]
    soma = float(diff.sum())
    n = len(alinhado)

    fator_anual = 365.0 / dias_cobertos
    bruto_aa = abs(soma) * fator_anual

    custo = 2 * (TAXA_TOMADOR[corretora_a] + TAXA_TOMADOR[corretora_b])
    liquido_aa_nocional = bruto_aa - custo * fator_anual
    liquido_aa_capital_implantado = liquido_aa_nocional / 2.0

    direcao = (f"short {corretora_a} / long {corretora_b}" if soma > 0
               else f"short {corretora_b} / long {corretora_a}")

    return ResultadoDiferencialCorretoras(
        corretora_a=corretora_a, corretora_b=corretora_b, par=par,
        dias_cobertos=dias_cobertos, n_periodos=n,
        diferencial_bruto_aa=bruto_aa,
        diferencial_liquido_aa_nocional=liquido_aa_nocional,
        diferencial_liquido_aa_capital_implantado=liquido_aa_capital_implantado,
        direcao=direcao,
        supera_benchmark=liquido_aa_capital_implantado > BENCHMARK_RENDA_FIXA_AA,
    )


def avaliar_universo(pares: Sequence[str] = ("BTC/USDT", "ETH/USDT"),
                      corretoras: Sequence[str] = CORRETORAS_QUALIFICADAS,
                      dias: int = DIAS_PADRAO) -> List[ResultadoDiferencialCorretoras]:
    resultados = []
    for par in pares:
        for corretora_a, corretora_b in combinations(corretoras, 2):
            r = avaliar_par_corretoras(corretora_a, corretora_b, par, dias=dias)
            if r is not None:
                resultados.append(r)
    return resultados
