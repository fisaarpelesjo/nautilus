"""H26 -- reversao contra funding extremo (crowding/liquidacao). Aposta
CONTRARIA a posicao majoritaria: funding extremamente NEGATIVO (shorts
crowded, pagando para manter a posicao) como gatilho de entrada LONG
contraria, avaliada pela mesma barreira tripla que H14 ja usa.
`specs/063-h26-reversao-funding-extremo/research.md` declara D1-D5 antes
de medir:

D1: limiar de extremo = decil mais negativo (10%) da distribuicao de
funding do PROPRIO par -- nao um valor absoluto compartilhado.

D2: so o lado long -- bot e long-only (CLAUDE.md), lado espelhado
(short) exigiria a mesma infraestrutura de futuros nunca construida
para producao (H8/H24).

D3: alinhamento funding (8h) -> candle (4h) por forward-fill causal --
cada candle herda a ultima leitura publicada ate aquele instante.

D4: limiar calibrado SO no treino, aplicado SEM reajuste na validacao;
significancia via supera_empate_com_confianca (Wilson CI) sobre a
contagem AGREGADA (pooled) entre pares -- nunca a razao pontual
isolada, nem o resultado de um par so.

D5: 2.000 candles de 4h (~333 dias) por par -- mesma janela do H14
pre-"historico estendido", por tratabilidade de tempo de execucao.

Diferente de H8/H23/H24 (carry continuo, aposta A FAVOR do sinal
observado e mantida) -- esta e uma aposta CONTRA o sinal, orientada a
evento extremo, ainda pertencente a familia DIRECIONAL que ja falhou em
21 avaliacoes anteriores deste registro (S6.3-b). Expectativa honesta
declarada: REPROVADA e o resultado mais provavel.
"""
from dataclasses import dataclass
from typing import List, Optional, Sequence

import pandas as pd

from backtesting.horizonte import UNIVERSO_H11, preparar
from backtesting.modelo import ParametrosBarreira, limiar_de_empate, supera_empate_com_confianca
from backtesting.validation import DEFAULT_VALIDATION_RATIO
from config.settings import TIMEFRAME
from data.fetcher import fetch_ohlcv
from data.funding import fetch_funding_rate_history
from strategy.barreira_tripla import rotular
from strategy.ema_rsi import EmaRsiStrategy

PERCENTIL_EXTREMO = 0.10  # decil mais negativo do funding -- D1
N_CANDLES = 2000  # ~333 dias em 4h -- D5
DIAS_FUNDING = 340  # cobre a janela de candles com folga -- D5


@dataclass
class ResultadoParH26:
    par: str
    limiar_extremo: float
    n_treino: int
    n_eventos_treino: int
    n_validacao: int
    n_eventos_validacao: int
    alvo_validacao: int
    stop_validacao: int
    razao_validacao: float
    supera_empate_validacao: bool


def _eventos_extremos(indice: pd.Index, funding: pd.Series, limiar_extremo: float) -> pd.Index:
    """Instantes de `indice` em que o funding alinhado (forward-fill
    causal -- D3) fica ABAIXO do limiar (mais negativo -- crowded
    short)."""
    funding_alinhado = funding.reindex(indice, method="ffill")
    return indice[funding_alinhado < limiar_extremo]


def avaliar_par(par: str, params: Optional[ParametrosBarreira] = None) -> Optional[ResultadoParH26]:
    """`None` quando o par nao tem mercado perpetuo, ou a serie nao e
    grande o bastante para dividir treino/validacao."""
    p = params or ParametrosBarreira()

    funding_df = fetch_funding_rate_history(par, dias=DIAS_FUNDING)
    if len(funding_df) == 0:
        return None
    funding_serie = funding_df["fundingRate"]

    df = fetch_ohlcv(par, TIMEFRAME, N_CANDLES)
    prep = preparar(df, EmaRsiStrategy())
    if prep is None or "atr" not in prep.columns:
        return None

    corte = int(len(prep) * (1 - DEFAULT_VALIDATION_RATIO))
    if corte <= 0 or corte >= len(prep):
        return None
    idx_treino = prep.index[:corte]
    idx_validacao = prep.index[corte:]

    funding_treino = funding_serie.reindex(idx_treino, method="ffill").dropna()
    if len(funding_treino) == 0:
        return None
    limiar_extremo = float(funding_treino.quantile(PERCENTIL_EXTREMO))

    rot = rotular(prep, p)["rotulo_bruto"]

    eventos_treino = _eventos_extremos(idx_treino, funding_serie, limiar_extremo)
    eventos_validacao = _eventos_extremos(idx_validacao, funding_serie, limiar_extremo)

    rot_validacao = rot.loc[eventos_validacao].dropna()
    n_alvo = int((rot_validacao == 1).sum())
    n_stop = int((rot_validacao == -1).sum())
    razao = n_alvo / n_stop if n_stop else float("inf")
    sig = supera_empate_com_confianca(n_alvo, n_stop, p) if n_stop else False

    return ResultadoParH26(
        par=par, limiar_extremo=limiar_extremo,
        n_treino=len(idx_treino), n_eventos_treino=len(eventos_treino),
        n_validacao=len(idx_validacao), n_eventos_validacao=len(eventos_validacao),
        alvo_validacao=n_alvo, stop_validacao=n_stop, razao_validacao=razao,
        supera_empate_validacao=sig,
    )


def avaliar_universo(pares: Optional[Sequence[str]] = None,
                      params: Optional[ParametrosBarreira] = None) -> List[ResultadoParH26]:
    pares = list(pares) if pares is not None else list(UNIVERSO_H11)
    resultados = []
    for par in pares:
        r = avaliar_par(par, params)
        if r is not None:
            resultados.append(r)
    return resultados


def agregar_pooled(resultados: List[ResultadoParH26],
                    params: Optional[ParametrosBarreira] = None) -> dict:
    """Agrega alvo/stop de validacao entre pares -- mesma logica de
    pooling de H14 (D4): razao de chances so tem poder estatistico
    agregada, por par a amostra costuma ser pequena demais."""
    p = params or ParametrosBarreira()
    n_alvo = sum(r.alvo_validacao for r in resultados)
    n_stop = sum(r.stop_validacao for r in resultados)
    razao = n_alvo / n_stop if n_stop else float("inf")
    sig = supera_empate_com_confianca(n_alvo, n_stop, p) if n_stop else False
    return {
        "n_pares": len(resultados), "n_alvo": n_alvo, "n_stop": n_stop,
        "razao": razao, "empate": limiar_de_empate(p), "supera_empate": sig,
    }
