"""H17 -- sinais on-chain, comparacao isolada BTC-only (spec 034).

NAO decide se H17 e aprovada -- reusa a bateria de avaliacao ja existente
de H14 (backtesting/modelo.py) sem alterar criterio, e compara, sobre o
MESMO par e MESMO periodo, o modelo original contra o modelo com o
atributo on-chain a mais (D-para-D, nunca contra o resultado pooled de 12
pares que H14 ja publicou -- ver specs/034-sinais-onchain/spec.md FR-005).
"""

from dataclasses import dataclass, field
from typing import Callable, Dict

import pandas as pd

from backtesting.modelo import AvaliacaoH14, avaliar_par
from config.settings import TIMEFRAME
from data.fetcher import fetch_ohlcv
from data.onchain import fetch_onchain_series
from strategy.barreira_tripla import ATRIBUTOS, extrair_atributos
from strategy.ema_rsi import EmaRsiStrategy

ATRIBUTO_ONCHAIN = "onchain_addr_growth_7d"


def onchain_addr_growth_7d(serie: pd.Series) -> pd.Series:
    """Variacao percentual de 7 dias da media movel de 7 dias (D1,
    research.md) -- declarada antes de qualquer medicao de correlacao ou
    desempenho, nao ajustada a um resultado."""
    ma7 = serie.rolling(7).mean()
    return (ma7 - ma7.shift(7)) / ma7.shift(7)


def _merge_causal(indice_candles: pd.DatetimeIndex, serie_diaria: pd.Series) -> pd.Series:
    """Para um candle no dia D, usa o valor do dia D-1 completo -- nunca o
    dia corrente, ainda incompleto na fonte (D5, research.md; mesma classe
    de correcao da spec 020 no MTF). Dia ausente leva adiante o ultimo
    conhecido (FR-009), nunca interpola."""
    indice_utc = indice_candles.tz_convert("UTC") if indice_candles.tz else indice_candles.tz_localize("UTC")
    serie_ordenada = serie_diaria.sort_index().dropna()

    valores = []
    for t in indice_utc:
        dia_disponivel = t.normalize() - pd.Timedelta(days=1)
        sub = serie_ordenada[serie_ordenada.index <= dia_disponivel]
        valores.append(sub.iloc[-1] if len(sub) else float("nan"))
    return pd.Series(valores, index=indice_candles)


def construir_extrator_onchain(serie_growth: pd.Series) -> Callable[[pd.DataFrame], pd.DataFrame]:
    """Fabrica que fecha sobre a serie de crescimento on-chain ja calculada
    e devolve uma funcao compativel com `extrair_atributos_fn` de
    `avaliar_par` (D4, research.md) -- os 5 atributos de H14, reusados sem
    alteracao, mais o atributo on-chain merged causalmente."""

    def extrator(prep: pd.DataFrame) -> pd.DataFrame:
        x = extrair_atributos(prep)
        x[ATRIBUTO_ONCHAIN] = _merge_causal(prep.index, serie_growth)
        return x

    return extrator


@dataclass
class RelatorioH17:
    avaliacao_base: AvaliacaoH14
    avaliacao_onchain: AvaliacaoH14
    correlacao_onchain: Dict[str, float] = field(default_factory=dict)
    atributo_declarado: str = ATRIBUTO_ONCHAIN


def avaliar_h17(par: str = "BTC/USDT") -> RelatorioH17:
    """Comparacao isolada: mesmo par, mesmo periodo, com e sem o atributo
    on-chain. Busca a serie e o historico uma unica vez, para as duas
    avaliacoes usarem exatamente o mesmo `df` (FR-005 -- nunca compara
    contra o resultado pooled de 12 pares ja publicado por H14)."""
    df = fetch_ohlcv(par, TIMEFRAME, 2000)
    onchain = fetch_onchain_series("n-unique-addresses", timespan="3years")
    serie_growth = onchain_addr_growth_7d(onchain["value"])

    avaliacao_base = avaliar_par(par, df=df)

    extrator = construir_extrator_onchain(serie_growth)
    avaliacao_onchain = avaliar_par(
        par, df=df,
        atributos=ATRIBUTOS + [ATRIBUTO_ONCHAIN],
        extrair_atributos_fn=extrator,
    )

    strategy = EmaRsiStrategy()
    prep = strategy.calculate_indicators(df)
    x_base = extrair_atributos(prep)
    x_onchain = _merge_causal(prep.index, serie_growth)
    completo = x_base.copy()
    completo[ATRIBUTO_ONCHAIN] = x_onchain
    completo = completo.dropna()
    correlacao = completo.corr()[ATRIBUTO_ONCHAIN].drop(ATRIBUTO_ONCHAIN).to_dict() if len(completo) else {}

    return RelatorioH17(
        avaliacao_base=avaliacao_base,
        avaliacao_onchain=avaliacao_onchain,
        correlacao_onchain=correlacao,
    )
