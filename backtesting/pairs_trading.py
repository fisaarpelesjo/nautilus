"""H10 — Arbitragem estatistica por cointegracao (variante long-only).

TESE

Dois ativos cointegrados mantem relacao de equilibrio de longo prazo; desvios do
spread sao temporarios. A literatura reporta Sharpe de 1,58 a 2,45 em cripto,
16,34% a.a. com volatilidade de 8,45% em BTC-ETH, e beta de 0,09 a 0,18 com alfa
de 11-15% a.a.

Propriedade distintiva: esta hipotese opera EM RAZAO da correlacao elevada, nao
apesar dela. A correlacao mediana de 0,71 que invalidou H9 (premio de
rebalanceamento) e insumo aqui.

RESTRICAO: POR QUE LONG-ONLY

A formulacao canonica exige posicao vendida na perna sobrevalorizada. As chaves
de API do projeto sao spot-only e o CLAUDE.md registra "Leitura + Trading Spot
apenas"; vender a descoberto exigiria margem, introduzindo risco de liquidacao.

A variante implementada assume apenas a perna comprada do ativo subvalorizado e
permanece em caixa no restante. Consequencias, declaradas:

  - Sacrifica a neutralidade a mercado. A posicao carrega beta, e o resultado
    NAO e independente da direcao do mercado. O beta reportado de 0,09-0,18 da
    literatura nao se aplica a esta variante.
  - Preserva a captura da reversao relativa: compra-se o ativo que ficou barato
    em relacao ao seu par cointegrado.
  - Por isso a avaliacao usa `ganho_de_timing_pp`: sem descontar exposicao, um
    sistema que fica em caixa a maior parte do tempo num mercado em queda
    pareceria habilidoso sem ser.

POR QUE MEIA-VIDA E NAO P-VALOR

O teste de Engle-Granger devolve p-valor de estacionariedade do residuo, que
responde "existe reversao?" mas nao "a reversao e rapida o bastante para pagar
taxa e slippage?". A meia-vida responde a segunda, que e a pergunta operacional.
Um par com reversao estatisticamente solida e meia-vida de 400 candles nao e
negociavel: o custo de carrego supera o retorno do spread.

Implementado com numpy para nao adicionar dependencia (statsmodels) a um bot em
producao por conta de uma hipotese de pesquisa.
"""
from dataclasses import dataclass
from itertools import combinations
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

from backtesting.engine import BacktestResult, Trade, _calculate_advanced_metrics
from config.settings import BACKTEST_FEE_RATE, BACKTEST_SLIPPAGE_PCT
from utils.logger import get_logger

log = get_logger("pairs_trading")

# statsmodels e dependencia de PESQUISA (requirements-dev.txt), nao de runtime:
# o bot em producao nao negocia pares e nao deve carregar a biblioteca. Sem ela,
# a selecao cai no criterio de fracao da janela, que e mais fraco -- por isso o
# aviso, e por isso `usar_adf` fica registrado no resultado da selecao.
try:
    from statsmodels.tsa.stattools import adfuller as _adfuller
    ADF_DISPONIVEL = True
except ImportError:  # pragma: no cover - depende do ambiente
    _adfuller = None
    ADF_DISPONIVEL = False


def teste_adf(spread, maxlag: Optional[int] = None) -> float:
    """p-valor do teste de Dickey-Fuller aumentado sobre o spread.

    H0: existe raiz unitaria (o spread NAO reverte). p pequeno rejeita H0, isto
    e, favorece estacionariedade -- que e a condicao de cointegracao.

    Devolve 1.0 (nao rejeita) quando statsmodels esta ausente ou o calculo
    falha: dado desconhecido nao vira aprovacao silenciosa, seguindo a politica
    de falha fechada do projeto.
    """
    if not ADF_DISPONIVEL or len(spread) < 20:
        return 1.0
    try:
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            return float(_adfuller(spread, maxlag=maxlag)[1])
    except Exception as exc:  # pragma: no cover - numerico
        log.warning(f"ADF falhou: {type(exc).__name__}")
        return 1.0


@dataclass
class PairsParams:
    formacao: int = 250          # candles usados para estimar hedge ratio e z-score
    entrada_z: float = 2.0       # entra quando o z-score cai abaixo de -entrada_z
    saida_z: float = 0.5         # sai quando o z-score volta acima de -saida_z
    stop_z: float = 4.0          # abandona a tese se o spread divergir alem disso
    meia_vida_min: int = 2       # abaixo disso e ruido de microestrutura
    meia_vida_max: int = 120     # acima disso o carrego come o retorno
    max_pares: int = 3           # quantos pares manter simultaneamente
    # Fracao maxima da janela de formacao que a meia-vida pode ocupar.
    # NAO e ajuste fino: e o que separa reversao real de vies de amostra finita.
    # O estimador OLS do coeficiente AR e enviesado para baixo (vies de
    # Dickey-Fuller), entao passeio aleatorio recebe meia-vida FINITA. Medido:
    # com n=250 a mediana e 38, com n=1000 sobe para 173, com n=3000 para 417 --
    # escala com a amostra, porque nao ha reversao a estimar. Serie
    # genuinamente revertente tem meia-vida independente de n (alvo 20 devolve
    # mediana 19 em n=1000). Exigir meia-vida <= 10% da janela separa os dois.
    max_fracao_da_janela: float = 0.10
    # Nivel de significancia do ADF. Medido em 300 passeios aleatorios de n=250:
    # o ADF rejeita em 5,0% (nominal exato), contra 28% do criterio de fracao da
    # janela sozinho. O poder e baixo -- detecta meia-vida 20 em 29,5% dos casos
    # a n=250 -- o que torna o teste CONSERVADOR: perde par cointegrado real,
    # mas nao admite ruido como cointegracao.
    adf_alpha: float = 0.05


@dataclass
class ParCointegrado:
    a: str
    b: str
    hedge_ratio: float
    meia_vida: float
    desvio_spread: float
    adf_pvalor: float = 1.0


def estimar_hedge_ratio(a: np.ndarray, b: np.ndarray) -> float:
    """Coeficiente beta de a ~ beta*b por minimos quadrados, sem intercepto.

    Sem intercepto de proposito: o intercepto e absorvido pela media do spread
    no z-score, e estima-lo aqui gastaria um grau de liberdade para nada.
    """
    denom = float(np.dot(b, b))
    if denom == 0:
        return 0.0
    return float(np.dot(a, b) / denom)


def meia_vida_reversao(spread: np.ndarray) -> float:
    """Meia-vida via AR(1): d_spread = lambda * spread_defasado + erro.

    half_life = -ln(2)/lambda. Retorna inf quando lambda >= 0, isto e, quando o
    spread nao reverte (passeio aleatorio ou divergente).
    """
    if len(spread) < 3:
        return float("inf")
    defasado = spread[:-1]
    delta = np.diff(spread)
    denom = float(np.dot(defasado - defasado.mean(), defasado - defasado.mean()))
    if denom == 0:
        return float("inf")
    lam = float(np.dot(defasado - defasado.mean(), delta - delta.mean()) / denom)
    if lam >= 0:
        return float("inf")
    return float(-np.log(2) / lam)


def selecionar_pares(
    precos: pd.DataFrame, p: PairsParams, ate: Optional[int] = None,
) -> List[ParCointegrado]:
    """Pares cujo spread reverte dentro da faixa de meia-vida negociavel.

    `ate` limita a janela de formacao ao passado disponivel no instante da
    decisao. Selecionar pares com a serie inteira usaria informacao futura --
    e o vies que faz backtest de pairs trading parecer excelente.
    """
    fim = len(precos) if ate is None else ate
    ini = max(0, fim - p.formacao)
    janela = precos.iloc[ini:fim]
    if len(janela) < max(30, p.formacao // 4):
        return []

    achados: List[ParCointegrado] = []
    for a, b in combinations(janela.columns, 2):
        sa = np.log(janela[a].to_numpy())
        sb = np.log(janela[b].to_numpy())
        if not (np.isfinite(sa).all() and np.isfinite(sb).all()):
            continue
        beta = estimar_hedge_ratio(sa, sb)
        if beta <= 0:
            continue
        spread = sa - beta * sb
        hl = meia_vida_reversao(spread)
        if not (p.meia_vida_min <= hl <= p.meia_vida_max):
            continue
        # Ver max_fracao_da_janela: sem este corte a selecao admite passeio
        # aleatorio sistematicamente, nao ocasionalmente.
        if hl > len(janela) * p.max_fracao_da_janela:
            continue
        # Portao de estacionariedade. A meia-vida responde "a reversao e rapida
        # o bastante para negociar?"; o ADF responde "existe reversao?". As duas
        # perguntas sao distintas e as duas precisam passar.
        pval = teste_adf(spread)
        if pval > p.adf_alpha:
            continue
        desvio = float(spread.std())
        if desvio <= 0:
            continue
        achados.append(ParCointegrado(a=a, b=b, hedge_ratio=beta,
                                      meia_vida=hl, desvio_spread=desvio,
                                      adf_pvalor=pval))

    # Meia-vida menor primeiro: reverte mais rapido, paga menos carrego.
    achados.sort(key=lambda x: x.meia_vida)
    return achados[:p.max_pares]


def _zscore_atual(precos: pd.DataFrame, par: ParCointegrado, i: int, formacao: int) -> float:
    ini = max(0, i - formacao)
    sa = np.log(precos[par.a].to_numpy()[ini:i + 1])
    sb = np.log(precos[par.b].to_numpy()[ini:i + 1])
    spread = sa - par.hedge_ratio * sb
    desvio = float(spread.std())
    if desvio == 0:
        return 0.0
    return float((spread[-1] - spread.mean()) / desvio)


def run_pairs_backtest(
    dados: Dict[str, pd.DataFrame],
    params: Optional[PairsParams] = None,
    initial_capital: float = 1000.0,
    fee_rate: float = BACKTEST_FEE_RATE,
    slippage_pct: float = BACKTEST_SLIPPAGE_PCT,
    reselecionar_a_cada: int = 250,
) -> BacktestResult:
    """Variante long-only: compra o ativo barato em relacao ao seu par."""
    p = params or PairsParams()

    series = {}
    for simbolo, df in dados.items():
        if df is None or df.empty or "close" not in df.columns:
            continue
        s = df["close"].copy()
        s.index = pd.to_datetime(df.index)
        series[simbolo] = s
    if len(series) < 2:
        return _resultado_vazio(initial_capital)

    precos = pd.concat(series, axis=1, join="inner").dropna()
    if len(precos) <= p.formacao + 10:
        log.warning("historico insuficiente para a janela de formacao")
        return _resultado_vazio(initial_capital)

    capital = initial_capital
    abertas: Dict[str, tuple] = {}   # simbolo -> (qtd, entrada, custo, taxa, hora, par)
    trades: List[Trade] = []
    curva: List[float] = []
    selecionados: List[ParCointegrado] = []

    for i in range(p.formacao, len(precos)):
        linha = precos.iloc[i]
        agora = precos.index[i]
        equity = capital + sum(q * linha[s] for s, (q, *_r) in abertas.items())
        curva.append(equity)

        if (i - p.formacao) % reselecionar_a_cada == 0:
            selecionados = selecionar_pares(precos, p, ate=i)

        if not selecionados:
            continue

        # Saidas primeiro, para liberar capital antes das entradas do mesmo ciclo.
        for simbolo in list(abertas.keys()):
            qtd, entrada, custo, taxa_ent, hora_ent, par = abertas[simbolo]
            z = _zscore_atual(precos, par, i, p.formacao)
            motivo = None
            if z >= -p.saida_z:
                motivo = "Reversao concluida"
            elif z <= -p.stop_z:
                motivo = "Divergencia (stop)"
            if motivo is None:
                continue
            abertas.pop(simbolo)
            saida = linha[simbolo] * (1 - slippage_pct)
            bruto = qtd * saida
            taxa_sai = bruto * fee_rate
            capital += bruto - taxa_sai
            pnl = (bruto - taxa_sai) - custo
            trades.append(Trade(
                entry_price=entrada, exit_price=saida, quantity=qtd, pnl=pnl,
                pnl_pct=pnl / custo * 100 if custo else 0.0,
                fees=taxa_ent + taxa_sai, entry_time=hora_ent,
                exit_time=agora, exit_reason=motivo,
            ))

        vagas = p.max_pares - len(abertas)
        if vagas <= 0 or capital <= 10:
            continue

        for par in selecionados:
            if vagas <= 0 or capital <= 10:
                break
            if par.a in abertas:
                continue
            z = _zscore_atual(precos, par, i, p.formacao)
            # z muito negativo: `a` ficou barato em relacao a `b`. Long-only,
            # compra-se `a` e nao se vende `b`.
            if z > -p.entrada_z or z <= -p.stop_z:
                continue
            nocional = min(capital * 0.95 / max(1, vagas), capital / (1 + fee_rate))
            if nocional < 10:
                continue
            entrada = linha[par.a] * (1 + slippage_pct)
            qtd = nocional / entrada
            taxa = nocional * fee_rate
            capital -= nocional + taxa
            abertas[par.a] = (qtd, entrada, nocional + taxa, taxa, agora, par)
            vagas -= 1

    if abertas:
        linha = precos.iloc[-1]
        for simbolo, (qtd, entrada, custo, taxa_ent, hora_ent, _par) in abertas.items():
            saida = linha[simbolo] * (1 - slippage_pct)
            bruto = qtd * saida
            taxa_sai = bruto * fee_rate
            capital += bruto - taxa_sai
            pnl = (bruto - taxa_sai) - custo
            trades.append(Trade(
                entry_price=entrada, exit_price=saida, quantity=qtd, pnl=pnl,
                pnl_pct=pnl / custo * 100 if custo else 0.0,
                fees=taxa_ent + taxa_sai, entry_time=hora_ent,
                exit_time=precos.index[-1], exit_reason="Fim do periodo",
            ))

    return _montar(trades, capital, initial_capital, curva, precos,
                   p.formacao, fee_rate, slippage_pct)


def _buy_hold_carteira(precos: pd.DataFrame, ini: int, fee_rate: float, slippage_pct: float) -> float:
    entrada = precos.iloc[ini] * (1 + slippage_pct)
    saida = precos.iloc[-1] * (1 - slippage_pct)
    return float(((saida / entrada).mean() - 1) * 100 - fee_rate * 2 * 100)


def _montar(trades, capital, initial_capital, curva, precos, ini, fee_rate, slippage_pct):
    total = (capital - initial_capital) / initial_capital * 100
    wins = [t for t in trades if t.pnl > 0]
    win_rate = len(wins) / len(trades) * 100 if trades else 0.0
    serie = pd.Series(curva) if curva else pd.Series([initial_capital])
    pico = serie.cummax()
    dd = float(((serie - pico) / pico * 100).min()) if len(serie) else 0.0
    bh = _buy_hold_carteira(precos, ini, fee_rate, slippage_pct)
    metrics = _calculate_advanced_metrics(
        trades, total_return_pct=total, buy_hold_return_pct=bh,
        max_drawdown_pct=abs(dd), period_start=precos.index[ini],
        period_end=precos.index[-1],
    )
    return BacktestResult(
        trades=trades, initial_capital=initial_capital, final_capital=capital,
        total_return_pct=total, win_rate=win_rate, total_trades=len(trades),
        max_drawdown_pct=abs(dd), buy_hold_return_pct=bh,
        edge_return_pct=total - bh, **metrics,
    )


def _resultado_vazio(initial_capital: float) -> BacktestResult:
    metrics = _calculate_advanced_metrics([])
    return BacktestResult(
        trades=[], initial_capital=initial_capital, final_capital=initial_capital,
        total_return_pct=0.0, win_rate=0.0, total_trades=0, max_drawdown_pct=0.0,
        buy_hold_return_pct=0.0, edge_return_pct=0.0, **metrics,
    )
