"""H14 -- calibracao do classificador: o subconjunto ja decidido em producao
(prob > limiar_de_decisao) tem razao de chances que sobrevive ao teste de
confianca do proprio projeto (supera_empate_com_confianca)? Um limiar mais
estrito concentra qualidade (razao sobe), ou so reduz a amostra sem melhorar
a razao? specs/055-h14-calibracao-classificador/research.md.

A linha de investigacao de overlays de risco (specs 040-047) fechou apontando
para duas frentes: o classificador de entrada em si, ou o mecanismo de saida.
Esta spec ataca a primeira -- pooled, sem tocar em nenhum parametro do
modelo, so agrupa previsoes ja calculadas (avaliar_par(..., retornar_previsao)
existente desde spec 037) por corte de probabilidade.
"""
from dataclasses import dataclass
from typing import List, Optional, Sequence

import pandas as pd

from backtesting.horizonte import UNIVERSO_H11, preparar
from backtesting.modelo import (
    ParametrosBarreira,
    avaliar_par,
    coletar_eventos,
    limiar_de_decisao,
    limiar_de_empate,
    supera_empate_com_confianca,
)
from config.settings import TIMEFRAME
from data.fetcher import fetch_ohlcv
from strategy.barreira_tripla import rotular
from strategy.ema_rsi import EmaRsiStrategy

# 0.0 e sentinela para "o limiar real de producao" (limiar_de_decisao), nao um
# corte literal em zero -- resolvido em avaliar_calibracao.
CORTES_PADRAO = (0.0, 0.35, 0.40, 0.45, 0.50, 0.55, 0.60)


@dataclass
class FaixaCalibracao:
    corte: float
    n: int
    alvo: int
    stop: int
    tempo: int
    razao: float
    supera_empate: bool


@dataclass
class ResultadoCalibracao:
    limiar_real: float
    empate: float
    n_pares: int
    faixas: List[FaixaCalibracao]


def _previsoes_pooladas(pares: Sequence[str], params: ParametrosBarreira):
    globais, _ = coletar_eventos(list(pares), params)

    previsoes, rotulos = [], []
    for par in pares:
        df = fetch_ohlcv(par, TIMEFRAME, 6000)
        a = avaliar_par(par, params, df=df,
                         eventos_globais=globais if len(globais) else None,
                         retornar_previsao=True)
        if a.previsao_teste is None:
            continue
        prep = preparar(df, EmaRsiStrategy())
        rot = rotular(prep, params)["rotulo_bruto"]
        idx = a.previsao_teste.index.intersection(rot.index)
        prev = a.previsao_teste.loc[idx]
        rb = rot.loc[idx].dropna()
        idx2 = prev.index.intersection(rb.index)
        previsoes.append(prev.loc[idx2])
        rotulos.append(rb.loc[idx2])

    if not previsoes:
        return None, None
    return pd.concat(previsoes), pd.concat(rotulos)


def _faixas_por_corte(prev_total: pd.Series, rot_total: pd.Series,
                       cortes: Sequence[float], limiar: float,
                       params: ParametrosBarreira) -> List[FaixaCalibracao]:
    """Pura: dadas as previsoes e rotulos ja pooled, agrupa por corte de
    probabilidade e mede a razao de chances REALIZADA em cada faixa.

    Separada de avaliar_calibracao para ser testavel sem buscar dado real
    (fetch_ohlcv/avaliar_par) -- mesmo principio do fixture `_modelo` em
    tests/test_modelo.py.
    """
    faixas = []
    for corte in cortes:
        corte_efetivo = limiar if corte == 0.0 else corte
        mask = prev_total > corte_efetivo
        sub = rot_total[mask]
        n_alvo = int((sub == 1).sum())
        n_stop = int((sub == -1).sum())
        n_tempo = int((sub == 0).sum())
        razao = n_alvo / n_stop if n_stop else float("inf")
        sig = supera_empate_com_confianca(n_alvo, n_stop, params) if n_stop else False
        faixas.append(FaixaCalibracao(corte=corte_efetivo, n=int(mask.sum()), alvo=n_alvo,
                                       stop=n_stop, tempo=n_tempo, razao=razao,
                                       supera_empate=sig))
    return faixas


def avaliar_calibracao(pares: Optional[Sequence[str]] = None,
                        params: Optional[ParametrosBarreira] = None,
                        cortes: Sequence[float] = CORTES_PADRAO) -> ResultadoCalibracao:
    p = params or ParametrosBarreira()
    pares = list(pares) if pares is not None else list(UNIVERSO_H11)
    limiar = limiar_de_decisao(p)
    empate = limiar_de_empate(p)

    prev_total, rot_total = _previsoes_pooladas(pares, p)
    if prev_total is None:
        return ResultadoCalibracao(limiar_real=limiar, empate=empate, n_pares=0, faixas=[])

    faixas = _faixas_por_corte(prev_total, rot_total, cortes, limiar, p)
    return ResultadoCalibracao(limiar_real=limiar, empate=empate, n_pares=len(pares),
                                faixas=faixas)
