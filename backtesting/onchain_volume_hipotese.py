"""H32 -- on-chain mais rico: valor transacionado, nao contagem de rede
(spec 069). Mede POSICIONAMENTO/magnitude (`estimated-transaction-volume-usd`)
em vez de atividade de rede (`n-unique-addresses`, ja testado por H17,
`insuficiente`). Mesma disciplina de H17: um atributo declarado, checagem
de colinearidade obrigatoria ANTES de qualquer leitura de desempenho,
comparacao isolada (nunca contra o pooled de 12 pares de H14).
"""

from dataclasses import dataclass, field
from typing import Dict, Optional

import pandas as pd

from backtesting.modelo import AvaliacaoH14, avaliar_par
from backtesting.onchain_hipotese import _merge_causal, onchain_addr_growth_7d
from config.settings import TIMEFRAME
from data.fetcher import fetch_ohlcv
from data.onchain import fetch_onchain_series
from strategy.barreira_tripla import ATRIBUTOS, extrair_atributos
from strategy.ema_rsi import EmaRsiStrategy

ATRIBUTO_VOLUME_ONCHAIN = "onchain_txn_volume_growth_7d"
METRICA_FONTE = "estimated-transaction-volume-usd"
LIMIAR_COLINEARIDADE = 0.80


def onchain_txn_volume_growth_7d(serie: pd.Series) -> pd.Series:
    """Mesma transformacao de `onchain_addr_growth_7d` (H17, D3 de
    research.md) -- so troca a serie de entrada, para isolar a variavel
    testada (o atributo) do metodo de transformacao."""
    return onchain_addr_growth_7d(serie)


def construir_extrator_volume(serie_growth: pd.Series) -> callable:
    def extrator(prep: pd.DataFrame) -> pd.DataFrame:
        x = extrair_atributos(prep)
        x[ATRIBUTO_VOLUME_ONCHAIN] = _merge_causal(prep.index, serie_growth)
        return x
    return extrator


@dataclass
class RelatorioH32:
    colinear: bool
    correlacao: Dict[str, float] = field(default_factory=dict)
    avaliacao_base: Optional[AvaliacaoH14] = None
    avaliacao_volume: Optional[AvaliacaoH14] = None
    atributo_declarado: str = ATRIBUTO_VOLUME_ONCHAIN


def avaliar_h32(par: str = "BTC/USDT") -> RelatorioH32:
    """Checa colinearidade primeiro (FR-002) -- so avalia desempenho
    (caro: retreina o modelo) se sobreviver ao limiar."""
    df = fetch_ohlcv(par, TIMEFRAME, 6000)
    onchain = fetch_onchain_series(METRICA_FONTE, timespan="3years")
    serie_growth = onchain_txn_volume_growth_7d(onchain["value"])

    onchain_addr = fetch_onchain_series("n-unique-addresses", timespan="3years")
    serie_addr_growth = onchain_addr_growth_7d(onchain_addr["value"])

    strategy = EmaRsiStrategy()
    prep = strategy.calculate_indicators(df)
    x_base = extrair_atributos(prep)
    x_base[ATRIBUTO_VOLUME_ONCHAIN] = _merge_causal(prep.index, serie_growth)
    x_base["onchain_addr_growth_7d"] = _merge_causal(prep.index, serie_addr_growth)
    completo = x_base.dropna()

    correlacao = {}
    if len(completo):
        correlacao = completo.corr()[ATRIBUTO_VOLUME_ONCHAIN].drop(ATRIBUTO_VOLUME_ONCHAIN).to_dict()

    colinear = any(abs(v) >= LIMIAR_COLINEARIDADE for v in correlacao.values())
    if colinear:
        return RelatorioH32(colinear=True, correlacao=correlacao)

    avaliacao_base = avaliar_par(par, df=df)
    extrator = construir_extrator_volume(serie_growth)
    avaliacao_volume = avaliar_par(
        par, df=df,
        atributos=ATRIBUTOS + [ATRIBUTO_VOLUME_ONCHAIN],
        extrair_atributos_fn=extrator,
    )

    return RelatorioH32(
        colinear=False, correlacao=correlacao,
        avaliacao_base=avaliacao_base, avaliacao_volume=avaliacao_volume,
    )
