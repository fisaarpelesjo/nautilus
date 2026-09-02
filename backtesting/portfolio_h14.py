"""Motor de carteira para aprovacao de H14 (spec 037).

Simula os pares de H14 com CAPITAL COMPARTILHADO e concorrencia real de
posicoes -- diferente de `avaliar_par`/`_simular`, que rodam cada par
isolado com seu proprio capital independente. E a unica forma de medir se
o risco de carteira (nao so o sinal estatistico por par) sustenta
aprovacao operacional de verdade (`docs/research/registro-de-hipoteses.md`
S4.15).

Reusa o mecanismo de saida do backtest JA PUBLICADO de H14 -- take-profit
por ATR e stop trailing (`_take_profit_price`/`_stop_price`/`_close_trade`,
`backtesting/engine.py`) -- nunca as barreiras de rotulagem do treino
(D7, `specs/037-motor-carteira-h14/research.md`): essas rotulam o alvo do
classificador, nao gerem a posicao no backtest real.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional

import pandas as pd

from backtesting.engine import (
    BacktestResult,
    Trade,
    _calculate_advanced_metrics,
    _close_trade,
    _stop_price,
    _take_profit_price,
)
from config.settings import (
    ATR_SL_MULTIPLIER,
    ATR_TP_MULTIPLIER,
    BACKTEST_FEE_RATE,
    BACKTEST_SLIPPAGE_PCT,
    MAX_ORDER_SIZE_USDT,
    MAX_POSITIONS,
    STOP_LOSS_PCT,
    TAKE_PROFIT_PCT,
    TIMEFRAME,
)


@dataclass
class PosicaoCarteira:
    """Espelha o estado por posicao de `simulate_backtest` -- um por par
    aberto simultaneamente (D7, research.md)."""

    par: str
    preco_entrada: float
    quantidade: float
    entry_atr: float
    entry_cost: float
    entry_fee: float
    preco_alvo: float
    stop_price: float
    highest_price: float
    instante_entrada: pd.Timestamp


@dataclass
class CarteiraH14:
    """Estado da simulacao -- caixa unico entre os pares (D1), no maximo
    `MAX_POSITIONS` posicoes simultaneas (FR-006)."""

    caixa: float
    posicoes: Dict[str, PosicaoCarteira] = field(default_factory=dict)
    curva_capital: List[tuple] = field(default_factory=list)


def _simular_carteira_core(
    previsoes: Dict[str, pd.Series],
    preparados: Dict[str, pd.DataFrame],
    limiar: float,
    capital_inicial: float = 1000.0,
    fee_rate: float = BACKTEST_FEE_RATE,
    slippage_pct: float = BACKTEST_SLIPPAGE_PCT,
) -> Optional[BacktestResult]:
    """Mecanica pura de carteira -- sem rede, sem treino. `previsoes[par]` e
    `preparados[par]` (colunas close/high/low/atr) MUST compartilhar o
    mesmo indice de timestamps (a janela de teste ja alinhada, D3).
    """
    pares_validos = [p for p in previsoes if len(previsoes[p]) > 0 and p in preparados]
    if not pares_validos:
        return None

    timeline = sorted(set().union(*(previsoes[p].index for p in pares_validos)))
    if not timeline:
        return None

    carteira = CarteiraH14(caixa=capital_inicial)
    trades: List[Trade] = []
    peak_equity = capital_inicial
    max_drawdown_pct = 0.0

    for t in timeline:
        # 1. Fecha posicoes que tocaram take-profit ou stop trailing (D7).
        for par in list(carteira.posicoes.keys()):
            prep = preparados[par]
            if t not in prep.index:
                continue
            row = prep.loc[t]
            pos = carteira.posicoes[par]
            exit_reason = None
            exit_price = row["close"] * (1 - slippage_pct)

            if row["low"] <= pos.stop_price:
                exit_reason = "Stop Loss"
                exit_price = pos.stop_price * (1 - slippage_pct)
            elif row["high"] >= pos.preco_alvo:
                exit_reason = "Take Profit"
                exit_price = pos.preco_alvo * (1 - slippage_pct)

            if exit_reason:
                carteira.caixa, trade = _close_trade(
                    carteira.caixa, pos.preco_entrada, exit_price, pos.quantidade,
                    pos.entry_cost, pos.entry_fee, pos.instante_entrada, t,
                    exit_reason, fee_rate,
                )
                trades.append(trade)
                del carteira.posicoes[par]
            elif row["high"] > pos.highest_price:
                pos.highest_price = row["high"]
                new_trail = pos.highest_price - ATR_SL_MULTIPLIER * pos.entry_atr
                if new_trail > pos.stop_price:
                    pos.stop_price = new_trail

        # 2. Candidatos a abrir: previsao acima do limiar, sem posicao aberta,
        # desempate pela maior probabilidade (D4).
        candidatos = []
        for par in pares_validos:
            if par in carteira.posicoes:
                continue
            previsao = previsoes[par]
            if t not in previsao.index:
                continue
            prob = previsao.loc[t]
            if prob > limiar:
                candidatos.append((prob, par))
        candidatos.sort(key=lambda item: item[0], reverse=True)

        for _prob, par in candidatos:
            slots_livres = MAX_POSITIONS - len(carteira.posicoes)
            if slots_livres <= 0:
                break
            if carteira.caixa < 10:
                break
            row = preparados[par].loc[t]
            order_size = min(MAX_ORDER_SIZE_USDT, (carteira.caixa / slots_livres) * 0.95)
            if order_size * (1 + fee_rate) > carteira.caixa:
                order_size = carteira.caixa / (1 + fee_rate)
            if order_size < 10:
                continue
            entry_price = row["close"] * (1 + slippage_pct)
            quantidade = order_size / entry_price
            entry_fee = order_size * fee_rate
            entry_cost = order_size + entry_fee
            entry_atr = float(row.get("atr", 0) or 0)
            carteira.caixa -= entry_cost
            carteira.posicoes[par] = PosicaoCarteira(
                par=par,
                preco_entrada=entry_price,
                quantidade=quantidade,
                entry_atr=entry_atr,
                entry_cost=entry_cost,
                entry_fee=entry_fee,
                preco_alvo=_take_profit_price(entry_price, entry_atr, TAKE_PROFIT_PCT, ATR_TP_MULTIPLIER),
                stop_price=_stop_price(entry_price, entry_atr, STOP_LOSS_PCT, ATR_SL_MULTIPLIER),
                highest_price=entry_price,
                instante_entrada=t,
            )

        # 3. Patrimonio deste candle: caixa + posicoes a mercado.
        valor_posicoes = sum(
            preparados[par].loc[t]["close"] * pos.quantidade
            for par, pos in carteira.posicoes.items()
            if t in preparados[par].index
        )
        patrimonio = carteira.caixa + valor_posicoes
        carteira.curva_capital.append((t, patrimonio))
        peak_equity = max(peak_equity, patrimonio)
        if peak_equity > 0:
            max_drawdown_pct = max(max_drawdown_pct, (peak_equity - patrimonio) / peak_equity * 100)

    # Fim do periodo: posicoes abertas fecham a mercado (mesmo rotulo do
    # motor generico, `_close_trade`/`simulate_backtest`).
    t_final = timeline[-1]
    for par, pos in list(carteira.posicoes.items()):
        prep = preparados[par]
        if t_final not in prep.index:
            continue
        exit_price = prep.loc[t_final]["close"] * (1 - slippage_pct)
        carteira.caixa, trade = _close_trade(
            carteira.caixa, pos.preco_entrada, exit_price, pos.quantidade,
            pos.entry_cost, pos.entry_fee, pos.instante_entrada, t_final,
            "Fim do periodo", fee_rate,
        )
        trades.append(trade)
    carteira.posicoes.clear()

    # Buy-and-hold de carteira: igualmente ponderada, sem rebalanceamento (D5).
    n = len(pares_validos)
    bh_final = 0.0
    fatia = capital_inicial / n
    for par in pares_validos:
        prep = preparados[par]
        if len(prep) == 0:
            bh_final += fatia
            continue
        preco_inicial = prep.iloc[0]["close"]
        preco_final = prep.iloc[-1]["close"]
        bh_final += fatia * (preco_final / preco_inicial) if preco_inicial else fatia
    buy_hold_return_pct = (bh_final - capital_inicial) / capital_inicial * 100

    final_capital = carteira.caixa
    total_return_pct = (final_capital - capital_inicial) / capital_inicial * 100
    win_rate = (len([t for t in trades if t.pnl > 0]) / len(trades) * 100) if trades else 0.0
    edge_return_pct = total_return_pct - buy_hold_return_pct

    metrics = _calculate_advanced_metrics(
        trades,
        total_return_pct=total_return_pct,
        buy_hold_return_pct=buy_hold_return_pct,
        max_drawdown_pct=max_drawdown_pct,
        period_start=timeline[0],
        period_end=timeline[-1],
    )

    return BacktestResult(
        trades=trades,
        initial_capital=capital_inicial,
        final_capital=final_capital,
        total_return_pct=total_return_pct,
        win_rate=win_rate,
        total_trades=len(trades),
        max_drawdown_pct=max_drawdown_pct,
        buy_hold_return_pct=buy_hold_return_pct,
        edge_return_pct=edge_return_pct,
        **metrics,
    )


def simular_carteira(pares=None, capital_inicial: float = 1000.0,
                     fee_rate: float = BACKTEST_FEE_RATE,
                     slippage_pct: float = BACKTEST_SLIPPAGE_PCT) -> Optional[BacktestResult]:
    """Busca dados reais, treina o modelo (`run_modelo_scan`, D2) e simula a
    carteira. Para testes sem rede, usar `_simular_carteira_core`
    diretamente."""
    from backtesting.horizonte import UNIVERSO_H11, preparar
    from backtesting.modelo import limiar_de_decisao, run_modelo_scan
    from data.fetcher import fetch_ohlcv
    from strategy.ema_rsi import EmaRsiStrategy

    pares = list(pares) if pares is not None else list(UNIVERSO_H11)
    avaliacoes = run_modelo_scan(pares, retornar_previsao=True)
    previsoes, preparados = _dados_da_carteira(avaliacoes, fetch_ohlcv, preparar, EmaRsiStrategy())

    return _simular_carteira_core(
        previsoes, preparados, limiar_de_decisao(), capital_inicial, fee_rate, slippage_pct,
    )


def _dados_da_carteira(avaliacoes, fetch_ohlcv_fn, preparar_fn, estrategia):
    """Monta `previsoes`/`preparados` a partir de `AvaliacaoH14` ja
    treinadas (`retornar_previsao=True`) -- fatiado exatamente na janela
    de teste ja definida por `avaliar_par` (D3)."""
    previsoes: Dict[str, pd.Series] = {}
    preparados: Dict[str, pd.DataFrame] = {}
    for a in avaliacoes:
        if a.previsao_teste is None or len(a.previsao_teste) == 0:
            continue
        df = fetch_ohlcv_fn(a.par, TIMEFRAME, 6000)
        prep = preparar_fn(df, estrategia)
        if prep is None:
            continue
        indice = a.previsao_teste.index.intersection(prep.index)
        if len(indice) == 0:
            continue
        previsoes[a.par] = a.previsao_teste.loc[indice]
        preparados[a.par] = prep.loc[indice]
    return previsoes, preparados


def comparar_drawdown(resultado_carteira: BacktestResult, avaliacoes: list) -> dict:
    """Drawdown agregado de carteira lado a lado com o maior drawdown por
    par isolado ja registrado em H14 -- nunca um substitui o outro (SC-003)."""
    por_par = {
        a.par: a.modelo.backtest.max_drawdown_pct
        for a in avaliacoes
        if a.modelo and a.modelo.backtest
    }
    return {
        "drawdown_carteira": resultado_carteira.max_drawdown_pct if resultado_carteira else None,
        "maior_drawdown_por_par": max(por_par.values()) if por_par else None,
        "drawdowns_por_par": por_par,
    }


__all__ = [
    "CarteiraH14",
    "PosicaoCarteira",
    "_dados_da_carteira",
    "_simular_carteira_core",
    "comparar_drawdown",
    "simular_carteira",
]
