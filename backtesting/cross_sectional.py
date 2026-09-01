"""Momentum transversal: ranqueia o universo de pares e mantem o topo.

POR QUE UM MOTOR SEPARADO

`backtesting/engine.py` avalia um par por vez, e `BaseStrategy.generate_signal`
recebe o DataFrame de um simbolo so. Momentum transversal nao cabe nessa
interface por definicao: a decisao de comprar BTC depende de como BTC se saiu
*em relacao a* ETH, SOL e aos demais no mesmo instante. Nenhuma quantidade de
sinal por par reproduz isso.

O que NAO muda: as metricas saem de `_calculate_advanced_metrics` do engine, o
resultado e um `BacktestResult` normal, e o veredito continua vindo de
`evaluate_approval`. A regua e a mesma -- so o motor e novo. Sem isso a
comparacao com EmaRsi/Breakout nao valeria nada.

A TESE

Liu et al. (2022) documentam que um modelo de tres fatores (mercado, tamanho,
momentum) explica o corte transversal de retornos em cripto, e que momentum
transversal e uma anomalia lucrativa. Replicacoes posteriores encontram
evidencia fraca, e o efeito aparece mais forte em periodos de alta atencao do
investidor -- ou seja, e uma hipotese a testar, nao um resultado assentado.

CUSTOS

Cada rebalanceamento vende o que saiu do topo e compra o que entrou, pagando
taxa e slippage nas duas pontas. Uma janela de rebalanceamento curta gira a
carteira toda com frequencia e o custo come o retorno -- e o motivo pelo qual
`rebalance_every` e o parametro mais sensivel aqui, mais que o lookback.
"""
from dataclasses import dataclass
from typing import Dict, List, Optional

import pandas as pd

from backtesting.engine import BacktestResult, Trade, _calculate_advanced_metrics
from config.settings import BACKTEST_FEE_RATE, BACKTEST_SLIPPAGE_PCT
from utils.logger import get_logger

log = get_logger("cross_sectional")


@dataclass
class CrossSectionalParams:
    lookback: int = 30          # candles usados para medir o momentum
    top_k: int = 3              # quantos pares manter na carteira
    rebalance_every: int = 6    # de quantos em quantos candles rebalancear
    min_momentum: float = 0.0   # so entra quem tiver retorno acima disso


def _alinhar(dados: Dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Matriz de precos de fechamento com um simbolo por coluna, alinhada no tempo.

    Simbolos sao listados na Binance em datas diferentes, entao a interseccao de
    timestamps e menor que a serie mais longa. Usar `join='inner'` de proposito:
    preencher buraco para trass faria o rank comparar preco real com preco
    repetido, e o par com dado faltando pareceria estavel justamente quando nao e.
    """
    series = {}
    for simbolo, df in dados.items():
        if df is None or df.empty or "close" not in df.columns:
            continue
        s = df["close"]
        s.index = pd.to_datetime(df.index)
        series[simbolo] = s
    if not series:
        return pd.DataFrame()
    return pd.concat(series, axis=1, join="inner").dropna()


def run_cross_sectional_backtest(
    dados: Dict[str, pd.DataFrame],
    params: Optional[CrossSectionalParams] = None,
    initial_capital: float = 1000.0,
    fee_rate: float = BACKTEST_FEE_RATE,
    slippage_pct: float = BACKTEST_SLIPPAGE_PCT,
) -> BacktestResult:
    """Roda momentum transversal sobre um conjunto de pares alinhados no tempo."""
    p = params or CrossSectionalParams()
    precos = _alinhar(dados)

    if precos.empty or len(precos) <= p.lookback + p.rebalance_every:
        log.warning("historico alinhado insuficiente para o transversal")
        return _resultado_vazio(initial_capital)

    capital = initial_capital
    # posicao aberta por simbolo: (quantidade, preco_de_entrada, custo, taxa, hora)
    carteira: Dict[str, tuple] = {}
    trades: List[Trade] = []
    curva: List[float] = []

    for i in range(p.lookback, len(precos)):
        linha = precos.iloc[i]
        agora = precos.index[i]

        # Patrimonio a mercado, para a curva de drawdown refletir posicao aberta
        # e nao so caixa -- foi exatamente essa confusao que fez a analise dos
        # trades reais reportar -49% de drawdown onde havia -4%.
        equity = capital + sum(q * linha[s] for s, (q, *_rest) in carteira.items())
        curva.append(equity)

        if (i - p.lookback) % p.rebalance_every != 0:
            continue

        janela = precos.iloc[i - p.lookback:i + 1]
        momentum = (janela.iloc[-1] / janela.iloc[0] - 1).sort_values(ascending=False)
        alvo = [s for s in momentum.index[:p.top_k] if momentum[s] > p.min_momentum]

        # Sai de quem nao esta mais no topo.
        for simbolo in list(carteira.keys()):
            if simbolo in alvo:
                continue
            qtd, entrada, custo, taxa_entrada, hora_entrada = carteira.pop(simbolo)
            saida = linha[simbolo] * (1 - slippage_pct)
            bruto = qtd * saida
            taxa_saida = bruto * fee_rate
            capital += bruto - taxa_saida
            pnl = (bruto - taxa_saida) - custo
            trades.append(Trade(
                entry_price=entrada, exit_price=saida, quantity=qtd,
                pnl=pnl, pnl_pct=pnl / custo * 100 if custo else 0.0,
                fees=taxa_entrada + taxa_saida,
                entry_time=hora_entrada, exit_time=agora,
                exit_reason="Rebalanceamento",
            ))

        # Entra em quem entrou no topo, dividindo o caixa entre as vagas livres.
        novos = [s for s in alvo if s not in carteira]
        vagas = p.top_k - len(carteira)
        if novos and vagas > 0 and capital > 10:
            por_vaga = (capital * 0.95) / vagas
            for simbolo in novos[:vagas]:
                if capital < 10:
                    break
                entrada = linha[simbolo] * (1 + slippage_pct)
                nocional = min(por_vaga, capital / (1 + fee_rate))
                qtd = nocional / entrada
                taxa = nocional * fee_rate
                capital -= nocional + taxa
                carteira[simbolo] = (qtd, entrada, nocional + taxa, taxa, agora)

    # Liquida o que sobrou aberto, como o engine faz no fim do periodo.
    if carteira:
        linha = precos.iloc[-1]
        for simbolo, (qtd, entrada, custo, taxa_entrada, hora_entrada) in carteira.items():
            saida = linha[simbolo] * (1 - slippage_pct)
            bruto = qtd * saida
            taxa_saida = bruto * fee_rate
            capital += bruto - taxa_saida
            pnl = (bruto - taxa_saida) - custo
            trades.append(Trade(
                entry_price=entrada, exit_price=saida, quantity=qtd,
                pnl=pnl, pnl_pct=pnl / custo * 100 if custo else 0.0,
                fees=taxa_entrada + taxa_saida,
                entry_time=hora_entrada, exit_time=precos.index[-1],
                exit_reason="Fim do periodo",
            ))

    return _montar_resultado(
        trades, capital, initial_capital, curva, precos, fee_rate, slippage_pct,
    )


def _buy_hold_carteira(precos: pd.DataFrame, fee_rate: float, slippage_pct: float) -> float:
    """Buy-and-hold de carteira igualmente ponderada em todos os pares.

    A referencia certa para uma estrategia de carteira e uma carteira, nao um
    unico par: comparar um sistema que roda 18 simbolos contra o buy-and-hold de
    BTC premiaria ou puniria a estrategia pela escolha do par de referencia.
    """
    entrada = precos.iloc[0] * (1 + slippage_pct)
    saida = precos.iloc[-1] * (1 - slippage_pct)
    retorno = ((saida / entrada).mean() - 1) * 100
    return retorno - fee_rate * 2 * 100


def _montar_resultado(trades, capital, initial_capital, curva, precos,
                      fee_rate, slippage_pct) -> BacktestResult:
    total_return = (capital - initial_capital) / initial_capital * 100
    wins = [t for t in trades if t.pnl > 0]
    win_rate = len(wins) / len(trades) * 100 if trades else 0.0

    serie = pd.Series(curva) if curva else pd.Series([initial_capital])
    pico = serie.cummax()
    max_dd = float(((serie - pico) / pico * 100).min()) if len(serie) else 0.0

    bh = _buy_hold_carteira(precos, fee_rate, slippage_pct)
    metrics = _calculate_advanced_metrics(
        trades,
        total_return_pct=total_return,
        buy_hold_return_pct=bh,
        max_drawdown_pct=abs(max_dd),
        period_start=precos.index[0],
        period_end=precos.index[-1],
    )
    return BacktestResult(
        trades=trades,
        initial_capital=initial_capital,
        final_capital=capital,
        total_return_pct=total_return,
        win_rate=win_rate,
        total_trades=len(trades),
        max_drawdown_pct=abs(max_dd),
        buy_hold_return_pct=bh,
        edge_return_pct=total_return - bh,
        **metrics,
    )


def _resultado_vazio(initial_capital: float) -> BacktestResult:
    metrics = _calculate_advanced_metrics([])
    return BacktestResult(
        trades=[], initial_capital=initial_capital, final_capital=initial_capital,
        total_return_pct=0.0, win_rate=0.0, total_trades=0, max_drawdown_pct=0.0,
        buy_hold_return_pct=0.0, edge_return_pct=0.0, **metrics,
    )

# --------------------------------------------------------------- walk-forward

@dataclass
class WalkForwardFold:
    """Resultado de uma janela do walk-forward."""
    janela: int
    buy_hold_pct: float
    retorno_pct: float
    exposicao_pct: float
    max_drawdown_pct: float
    trades: int

    @property
    def regime(self) -> str:
        if self.buy_hold_pct > 5:
            return "alta"
        return "baixa" if self.buy_hold_pct < -5 else "lado"

    @property
    def passivo_pct(self) -> float:
        """Buy-and-hold mantido na MESMA fracao de capital, sem nenhum timing.

        E a referencia certa para uma estrategia que fica parcialmente em caixa:
        sem ela, "perdi 6% enquanto o mercado caiu 55%" parece habilidade quando
        pode ser apenas nao ter estado la.
        """
        return self.buy_hold_pct * (self.exposicao_pct / 100)

    @property
    def ganho_de_timing_pp(self) -> float:
        """Quanto a ESCOLHA dos ativos rendeu, descontada a reducao de exposicao."""
        return self.retorno_pct - self.passivo_pct


def walk_forward(
    dados: Dict[str, pd.DataFrame],
    params: CrossSectionalParams,
    n_janelas: int = 5,
    initial_capital: float = 1000.0,
) -> List[WalkForwardFold]:
    """Roda a mesma configuracao em janelas contiguas e nao sobrepostas.

    Por que existe: uma janela unica de confirmacao nao distingue vantagem de
    sorte de regime. Uma configuracao desta estrategia mediu +29pp de edge numa
    janela e, nas cinco janelas, entregou ganho de timing MEDIO negativo -- o
    resultado bom era a janela, nao a estrategia.

    Nao seleciona nada: recebe uma configuracao pronta e informa como ela se
    comporta em cada regime. Escolher a melhor de uma varredura grande e o
    mecanismo que produz vantagem inexistente.
    """
    if not dados:
        return []
    n = min(len(v) for v in dados.values())
    tam = n // max(1, n_janelas)
    if tam <= params.lookback:
        log.warning("janelas menores que o lookback -- walk-forward nao aplicavel")
        return []

    folds: List[WalkForwardFold] = []
    for j in range(n_janelas):
        fatia = {k: v.iloc[j * tam:(j + 1) * tam] for k, v in dados.items()}
        r = run_cross_sectional_backtest(fatia, params, initial_capital=initial_capital)
        folds.append(WalkForwardFold(
            janela=j + 1,
            buy_hold_pct=r.buy_hold_return_pct,
            retorno_pct=r.total_return_pct,
            exposicao_pct=r.exposure_pct,
            max_drawdown_pct=r.max_drawdown_pct,
            trades=r.total_trades,
        ))
    return folds


def resumir_walk_forward(folds: List[WalkForwardFold]) -> dict:
    """Consolida o walk-forward. A media do ganho de timing e o numero que decide."""
    if not folds:
        return {"janelas": 0}
    ganhos = [f.ganho_de_timing_pp for f in folds]
    return {
        "janelas": len(folds),
        "timing_medio_pp": sum(ganhos) / len(ganhos),
        "timing_pior_pp": min(ganhos),
        "janelas_com_timing_positivo": sum(1 for g in ganhos if g > 0),
        "retorno_medio_pct": sum(f.retorno_pct for f in folds) / len(folds),
        "drawdown_maximo_pct": max(f.max_drawdown_pct for f in folds),
    }
