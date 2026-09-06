"""H38 -- gate por volatilidade implicita (Deribit DVOL), spec 074.
Verifica se DVOL (volatilidade implicita de 30 dias de BTC, mercado de
OPCOES) DISCRIMINA eventos de entrada bons de ruins do sinal primario
(EMA/RSI, producao) -- precondicao antes de declarar qualquer aprovacao
de um gate aditivo completo, mesmo desenho de
`backtesting/meta_labeling.py::avaliar_precondicao` (H27). Ver
`specs/074-h38-dvol-gate/research.md` para D1-D5 declarados ANTES de
qualquer medicao:

D1: precondicao atendida <=> razao(resto) > razao(dvol_alto) -- direcao
declarada antes de medir (DVOL alto discrimina para PIOR).

D2: numero de partida ja publicado por H27 sobre a MESMA populacao:
n=740, razao=0.5011, nao supera empate. Reportado aqui so como
comparacao (FR-009), nao recalculado.

D3: decil mais alto (90) da propria serie de DVOL -- nao um valor
absoluto.

D4: alinhamento causal D-1, evento sem DVOL alinhavel e EXCLUIDO, nunca
presumido.

D5: retencao real do DVOL medida por probe (901 dias, 2024-03-19 em
diante) -- eventos antes disso sao excluidos da divisao, sem afetar o
numero ja publicado de H27.

Reconstroi a extracao de eventos com os MESMOS blocos que
`meta_labeling.py` ja usa (EmaRsiStrategy, precompute_signals, rotular,
UNIVERSO_H11) em vez de importar do modulo H27 -- H27 e modulo ja
publicado/citado (spec 064), e alterar seu conteudo para expor os
rotulos brutos por evento arriscaria mudar um numero ja citado sem
necessidade (licao de M1, registro S5). `meta_labeling.avaliar_precondicao`
e apenas CHAMADO (nao alterado) para reportar seu numero ja publicado
lado a lado.
"""
from dataclasses import dataclass
from typing import List, Optional, Sequence

import pandas as pd

from backtesting.engine import precompute_signals
from backtesting.horizonte import UNIVERSO_H11, preparar
from backtesting.meta_labeling import ResultadoPrecondicao, avaliar_precondicao
from backtesting.modelo import ParametrosBarreira, limiar_de_empate, supera_empate_com_confianca
from config.settings import TIMEFRAME
from data.deribit import fetch_dvol_history
from data.fetcher import fetch_ohlcv
from strategy.barreira_tripla import rotular
from strategy.base import Signal
from strategy.ema_rsi import EmaRsiStrategy

PERCENTIL_ALTO_DVOL = 0.90  # decil mais alto = stress -- D3


def _alinhar_causal(indice_eventos: pd.DatetimeIndex, serie_diaria: pd.Series) -> pd.Series:
    """Para um evento no dia D, usa o valor do dia D-1 completo -- nunca o
    dia corrente, ainda incompleto na fonte. Dia ausente e NaN (D4) --
    diferente de H17/H32/H36 (forward-fill de um dado sempre disponivel
    no periodo), aqui a ausencia e um resultado esperado (retencao do
    DVOL menor que o historico de candles) e deve ficar visivel, nao
    escondida atras de um ultimo valor levado adiante indefinidamente."""
    indice_utc = indice_eventos.tz_convert("UTC") if indice_eventos.tz else indice_eventos.tz_localize("UTC")
    serie_ordenada = serie_diaria.sort_index().dropna()
    serie_ordenada = serie_ordenada[~serie_ordenada.index.duplicated(keep="last")]

    # reindex por EXATAMENTE o dia D-1 -- diferente de um "ultimo valor <=
    # D-1" (que levaria adiante um valor antigo por cima de um buraco
    # interno na serie), um dia D-1 ausente vira NaN mesmo que exista
    # valor mais antigo, exatamente o contrato declarado acima.
    dias_disponiveis = indice_utc.normalize() - pd.Timedelta(days=1)
    valores = serie_ordenada.reindex(dias_disponiveis).to_numpy()
    return pd.Series(valores, index=indice_eventos)


@dataclass
class ResultadoFaixaDVOL:
    nome: str
    n: int
    alvo: int
    stop: int
    razao: float
    supera_empate: bool


def _resumo(rot: pd.Series, nome: str, params: ParametrosBarreira) -> ResultadoFaixaDVOL:
    alvo = int((rot == 1).sum())
    stop = int((rot == -1).sum())
    razao = alvo / stop if stop else float("inf")
    sig = supera_empate_com_confianca(alvo, stop, params) if stop else False
    return ResultadoFaixaDVOL(nome=nome, n=len(rot), alvo=alvo, stop=stop, razao=razao, supera_empate=sig)


@dataclass
class ResultadoPrecondicaoDVOL:
    empate: float
    limiar_dvol: float
    n_pares_com_dvol: int
    baseline_h27: ResultadoPrecondicao
    dvol_alto: ResultadoFaixaDVOL
    resto: ResultadoFaixaDVOL
    precondicao_atendida: bool


def avaliar_precondicao_dvol(pares: Optional[Sequence[str]] = None,
                              params: Optional[ParametrosBarreira] = None) -> ResultadoPrecondicaoDVOL:
    p = params or ParametrosBarreira()
    pares = list(pares) if pares is not None else list(UNIVERSO_H11)
    empate = limiar_de_empate(p)

    dvol_serie = fetch_dvol_history("BTC")["close"]
    limiar_dvol = float(dvol_serie.quantile(PERCENTIL_ALTO_DVOL))

    rot_dvol_alto: List[pd.Series] = []
    rot_resto: List[pd.Series] = []
    n_pares_com_dvol = 0

    for par in pares:
        df = fetch_ohlcv(par, TIMEFRAME, 6000)
        estrategia = EmaRsiStrategy()
        prep = preparar(df, estrategia)
        if prep is None:
            continue
        sinais = precompute_signals(prep, estrategia)
        entradas = (sinais == Signal.BUY).to_numpy()
        rot = rotular(prep, p)["rotulo_bruto"]
        validos = rot.notna().to_numpy()
        eventos_idx = prep.index[entradas & validos]
        if len(eventos_idx) == 0:
            continue

        dvol_nos_eventos = _alinhar_causal(eventos_idx, dvol_serie)
        com_dvol = dvol_nos_eventos.notna()
        if not com_dvol.any():
            continue
        n_pares_com_dvol += 1

        eventos_com_dvol = eventos_idx[com_dvol.to_numpy()]
        alto = (dvol_nos_eventos[com_dvol] >= limiar_dvol).to_numpy()

        rot_dvol_alto.append(rot.loc[eventos_com_dvol[alto]])
        rot_resto.append(rot.loc[eventos_com_dvol[~alto]])

    if n_pares_com_dvol == 0:
        raise ValueError("nenhum par produziu evento de entrada com DVOL alinhavel")

    resumo_alto = _resumo(
        pd.concat(rot_dvol_alto) if rot_dvol_alto else pd.Series(dtype=float),
        "dvol alto (decil 90+)", p,
    )
    resumo_resto = _resumo(
        pd.concat(rot_resto) if rot_resto else pd.Series(dtype=float),
        "resto", p,
    )
    baseline_h27 = avaliar_precondicao(pares, params)

    return ResultadoPrecondicaoDVOL(
        empate=empate, limiar_dvol=limiar_dvol, n_pares_com_dvol=n_pares_com_dvol,
        baseline_h27=baseline_h27, dvol_alto=resumo_alto, resto=resumo_resto,
        precondicao_atendida=resumo_resto.razao > resumo_alto.razao,
    )
