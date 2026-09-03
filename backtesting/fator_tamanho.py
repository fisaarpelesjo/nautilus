"""H30 -- fator de tamanho/iliquidez (cross-sectional, sem timing).
`specs/067-h30-fator-tamanho-iliquidez/research.md` declara D1-D5 antes
de qualquer medicao:

D1 (universo): `UNIVERSO_AMPLO_HISTORICO_COMPLETO` (`backtesting/
pairs_trading.py`, 22 pares com historico completo de 6.000 candles ja
confirmado -- evita o bug de colapso de indice comum que ja pegou H10,
spec 052) -- nao escolhido para este teste, ja existente.

D2 (construcao da cesta): igualmente ponderada, N=7 pares (~1/3 de 22),
rebalanceada a cada 180 candles (30 dias em 4h) -- declarado antes de
medir, nao ajustado depois do resultado.

D3 (baseline de comparacao): a MESMA construcao sobre os 7 pares de
MAIOR volume (cesta liquida) -- isola o efeito de tamanho/liquidez em
vez de "uma cesta de altcoins subiu".

D4 (custo -- limitacao declarada): backtest historico nao tem order
book do passado (CLAUDE.md ja documenta isso para REAL_SLIPPAGE_ENABLED)
-- a medicao real de slippage por liquidez, como H14/H8 fazem em paper
mode, nao e possivel aqui. Em vez de fingir uma medicao que nao existe,
o custo de giro (turnover) de cada rebalanceamento e medido sob TRES
multiplicadores do slippage padrao (1x, 3x, 5x `BACKTEST_SLIPPAGE_PCT`)
-- sensibilidade declarada, nao um numero unico otimista.

D5 (disciplina fora da amostra): mesmo corte compartilhado de H10
(`split_treino_validacao`) -- o excesso de retorno da cesta iliquida
sobre a liquida precisa aparecer nos dois lados do corte, nao so no
treino, para nao repetir o padrao "so na busca" de H5.
"""
from dataclasses import dataclass
from typing import Dict, List

import pandas as pd

from backtesting.pairs_trading import UNIVERSO_AMPLO_HISTORICO_COMPLETO, split_treino_validacao
from config.settings import BACKTEST_FEE_RATE, BACKTEST_SLIPPAGE_PCT

N_CESTA = 7  # ~1/3 de 22 pares (D2)
REBALANCE_A_CADA = 180  # 30 dias em candles de 4h (D2)
MULTIPLICADORES_SLIPPAGE = (1.0, 3.0, 5.0)  # D4


@dataclass
class ResultadoCesta:
    criterio: str
    pares: List[str]
    n_rebalanceamentos: int
    capital_inicial: float
    capital_final: float
    retorno_pct: float
    drawdown_max_pct: float
    custo_total_turnover: float
    multiplicador_slippage: float


def _volume_medio_usdt(df: pd.DataFrame) -> float:
    return float((df["close"] * df["volume"]).mean())


def selecionar_cesta(dados: Dict[str, pd.DataFrame], n: int, criterio: str) -> List[str]:
    """`criterio`: 'menor_volume' (iliquida) ou 'maior_volume' (liquida,
    baseline de comparacao, D3). Volume medio calculado sobre o proprio
    `dados` recebido -- treino e validacao podem reordenar a cesta,
    reflete o que seria observavel em cada janela, nao um ranking fixo
    do futuro."""
    volumes = {par: _volume_medio_usdt(df) for par, df in dados.items() if len(df) > 0}
    ordenado = sorted(volumes, key=lambda p: volumes[p], reverse=(criterio == "maior_volume"))
    return ordenado[:n]


def simular_cesta(dados: Dict[str, pd.DataFrame], pares: List[str], criterio: str,
                   capital_inicial: float = 1000.0,
                   rebalance_a_cada: int = REBALANCE_A_CADA,
                   fee_rate: float = BACKTEST_FEE_RATE,
                   slippage_pct: float = BACKTEST_SLIPPAGE_PCT,
                   multiplicador_slippage: float = 1.0) -> ResultadoCesta:
    """Cesta igualmente ponderada, rebalanceada a cada `rebalance_a_cada`
    candles -- sem sinal de entrada/saida, sem timing. Custo pago sobre o
    GIRO (turnover) de cada rebalanceamento, nunca sobre o nocional
    inteiro reaberto do zero."""
    pares_validos = [p for p in pares if p in dados and len(dados[p]) > 0]
    if not pares_validos:
        return ResultadoCesta(criterio, [], 0, capital_inicial, capital_inicial, 0.0, 0.0, 0.0,
                               multiplicador_slippage)

    timeline = sorted(set().union(*(dados[p].index for p in pares_validos)))
    if not timeline:
        return ResultadoCesta(criterio, pares_validos, 0, capital_inicial, capital_inicial, 0.0,
                               0.0, 0.0, multiplicador_slippage)

    n = len(pares_validos)
    peso_alvo = 1.0 / n
    custo_efetivo = fee_rate + slippage_pct * multiplicador_slippage
    quantidades = {p: 0.0 for p in pares_validos}
    caixa = capital_inicial
    custo_total = 0.0
    n_rebal = 0
    peak = capital_inicial
    max_dd = 0.0

    def _preco(par, t):
        df = dados[par]
        return float(df.loc[t, "close"]) if t in df.index else None

    def _valor_total(t):
        v = caixa
        for p in pares_validos:
            preco = _preco(p, t)
            if preco is not None:
                v += quantidades[p] * preco
        return v

    for i, t in enumerate(timeline):
        if i == 0 or i % rebalance_a_cada == 0:
            n_rebal += 1
            valor_total = _valor_total(t)
            alvo_por_ativo = valor_total * peso_alvo
            precos = {p: _preco(p, t) for p in pares_validos}

            # 1a passada: vende excesso (levanta caixa) antes de comprar.
            for p in pares_validos:
                preco = precos[p]
                if preco is None:
                    continue
                diferenca = alvo_por_ativo - quantidades[p] * preco
                if diferenca < -1e-9:
                    qtd_vender = min(abs(diferenca) / preco, quantidades[p])
                    custo = qtd_vender * preco * custo_efetivo
                    quantidades[p] -= qtd_vender
                    caixa += qtd_vender * preco - custo
                    custo_total += custo

            # 2a passada: compra o que falta, limitado ao caixa disponivel.
            for p in pares_validos:
                preco = precos[p]
                if preco is None:
                    continue
                diferenca = alvo_por_ativo - quantidades[p] * preco
                if diferenca > 1e-9:
                    gasto_desejado = diferenca * (1 + custo_efetivo)
                    gasto = min(gasto_desejado, caixa)
                    if gasto <= 0:
                        continue
                    custo = gasto * custo_efetivo / (1 + custo_efetivo)
                    qtd_comprar = (gasto - custo) / preco
                    quantidades[p] += qtd_comprar
                    caixa -= gasto
                    custo_total += custo

        valor = _valor_total(t)
        peak = max(peak, valor)
        if peak > 0:
            max_dd = max(max_dd, (peak - valor) / peak * 100)

    capital_final = _valor_total(timeline[-1])
    retorno_pct = (capital_final - capital_inicial) / capital_inicial * 100

    return ResultadoCesta(
        criterio=criterio, pares=pares_validos, n_rebalanceamentos=n_rebal,
        capital_inicial=capital_inicial, capital_final=capital_final,
        retorno_pct=retorno_pct, drawdown_max_pct=max_dd, custo_total_turnover=custo_total,
        multiplicador_slippage=multiplicador_slippage,
    )


def avaliar_fator_tamanho(pares: List[str] = None, n: int = N_CESTA,
                           rebalance_a_cada: int = REBALANCE_A_CADA,
                           dados: Dict[str, pd.DataFrame] = None):
    """Compara cesta iliquida vs liquida, treino e validacao, sob os tres
    multiplicadores de slippage declarados (D4). `dados` opcional permite
    teste sem rede (mesmo padrao de `avaliar_par(df=...)`, H14)."""
    from config.settings import TIMEFRAME
    from data.fetcher import fetch_ohlcv

    pares = list(pares) if pares is not None else list(UNIVERSO_AMPLO_HISTORICO_COMPLETO)

    if dados is None:
        dados = {p: fetch_ohlcv(p, TIMEFRAME, 6000) for p in pares}

    dados_treino, dados_validacao = split_treino_validacao(dados, formacao=REBALANCE_A_CADA)

    resultados = {}
    for fatia_nome, fatia in (("treino", dados_treino), ("validacao", dados_validacao)):
        for criterio in ("menor_volume", "maior_volume"):
            cesta = selecionar_cesta(fatia, n, criterio)
            for mult in MULTIPLICADORES_SLIPPAGE:
                r = simular_cesta(fatia, cesta, criterio, rebalance_a_cada=rebalance_a_cada,
                                   multiplicador_slippage=mult)
                resultados[(fatia_nome, criterio, mult)] = r

    return resultados
