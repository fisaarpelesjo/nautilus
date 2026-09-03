"""H27 -- meta-labeling: pré-condição (D1) verifica se o sinal PRIMÁRIO
(EMA/RSI, produção) carrega informação real nos próprios eventos de
entrada, antes de treinar um modelo SECUNDÁRIO para filtrá-los.
`specs/064-h27-meta-labeling/research.md` declara o critério antes de
medir: se os eventos de entrada do sinal primário não superam o empate
com confiança (mesmo teste de H14, Wilson CI), não há informação a
filtrar -- mesma família de bloqueio por pré-condição de H12 (§6.4 do
registro).
"""
from dataclasses import dataclass
from typing import List, Optional, Sequence

import pandas as pd

from backtesting.engine import precompute_signals
from backtesting.horizonte import UNIVERSO_H11, preparar
from backtesting.modelo import limiar_de_empate, supera_empate_com_confianca
from config.settings import TIMEFRAME
from data.fetcher import fetch_ohlcv
from strategy.barreira_tripla import ParametrosBarreira, rotular
from strategy.base import Signal
from strategy.ema_rsi import EmaRsiStrategy


@dataclass
class ResultadoFaixa:
    nome: str
    n: int
    alvo: int
    stop: int
    tempo: int
    razao: float
    supera_empate: bool


@dataclass
class ResultadoPrecondicao:
    empate: float
    n_pares: int
    baseline: ResultadoFaixa
    entrada_primaria: ResultadoFaixa
    precondicao_atendida: bool


def _resumo(rot: pd.Series, nome: str, params: ParametrosBarreira) -> ResultadoFaixa:
    alvo = int((rot == 1).sum())
    stop = int((rot == -1).sum())
    tempo = int((rot == 0).sum())
    razao = alvo / stop if stop else float("inf")
    sig = supera_empate_com_confianca(alvo, stop, params) if stop else False
    return ResultadoFaixa(nome=nome, n=len(rot), alvo=alvo, stop=stop, tempo=tempo,
                           razao=razao, supera_empate=sig)


def avaliar_precondicao(pares: Optional[Sequence[str]] = None,
                         params: Optional[ParametrosBarreira] = None) -> ResultadoPrecondicao:
    """D1: os eventos de entrada do sinal primário (EMA/RSI) superam o
    empate com confiança? Se não, meta-labeling não é testável -- não há
    informação no sinal primário para um modelo secundário filtrar.

    Compara dois subconjuntos do MESMO rótulo de barreira tripla
    (`rotular`, os 5 atributos de H14 não entram aqui -- esta pré-condição
    é sobre o sinal primário puro, não sobre um classificador): todos os
    candles rotuláveis (baseline) contra só os candles em que o sinal
    primário (EMA/RSI, `precompute_signals`) já emitiria BUY.
    """
    p = params or ParametrosBarreira()
    pares = list(pares) if pares is not None else list(UNIVERSO_H11)
    empate = limiar_de_empate(p)

    rotulos_geral: List[pd.Series] = []
    rotulos_entrada: List[pd.Series] = []
    for par in pares:
        df = fetch_ohlcv(par, TIMEFRAME, 6000)
        estrategia = EmaRsiStrategy()
        prep = preparar(df, estrategia)
        if prep is None:
            continue
        sinais = precompute_signals(prep, estrategia)
        entradas = sinais == Signal.BUY
        rot = rotular(prep, p)["rotulo_bruto"]
        validos = rot.notna()
        rotulos_geral.append(rot[validos])
        rotulos_entrada.append(rot[entradas & validos])

    if not rotulos_geral:
        raise ValueError("nenhum par produziu dado rotulavel")

    rot_geral = pd.concat(rotulos_geral)
    rot_entrada = pd.concat(rotulos_entrada)

    baseline = _resumo(rot_geral, "baseline (todos os candles)", p)
    entrada = _resumo(rot_entrada, "entrada primaria (EMA/RSI)", p)

    return ResultadoPrecondicao(
        empate=empate, n_pares=len(pares), baseline=baseline,
        entrada_primaria=entrada, precondicao_atendida=entrada.supera_empate,
    )
