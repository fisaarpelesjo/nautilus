"""H29 -- pairs trading via cópula gaussiana (dependência não-linear).

H10 (`backtesting/pairs_trading.py`) mede a distância entre os dois
preços via z-score sobre um spread linear (`log(a) - beta*log(b)`).
Aqui a pergunta é diferente: será que modelar a distribuição conjunta
completa dos RETORNOS via cópula -- capturando dependência de cauda que
o z-score linear não vê -- produz um sinal de entrada/saída melhor
sobre os MESMOS pares cointegrados? `selecionar_pares`/`PairsParams` de
H10 são reusados sem alteração para a seleção -- a pergunta desta spec
é só sobre o sinal, não sobre quais pares são cointegrados
(`specs/066-h29-pairs-copula/research.md` D1: precondição verificada
antes de qualquer código -- os pares de H10 cointegram de verdade,
H10 foi reprovada pelo sinal, não pela ausência de relação).

Método (Tadi & Witzany 2025, `docs/research/copula-based-trading-of-
cointegrated-cryptocurrency-pairs.md`, "return-based copula method",
Eq. 4): fita cópula gaussiana sobre os retornos das duas pernas na
janela de formação (marginais via CDF empírica -- Sklar, sem assumir
forma paramétrica), calcula a distribuição condicional
h(u1|u2) = P(U1 <= u1 | U2 = u2) em forma fechada para cada candle
novo. h1|2 próximo de 0 sinaliza que o retorno de `a` está anormalmente
baixo dado o retorno de `b` -- `a` ficou barato em relação a `b`.
"""
from dataclasses import dataclass
from typing import Dict, List, Optional

import numpy as np
import pandas as pd
from scipy.stats import norm

from backtesting.engine import BacktestResult, Trade, _calculate_advanced_metrics
from backtesting.pairs_trading import (
    ParCointegrado,
    PairsParams,
    _buy_hold_carteira,
    selecionar_pares,
)
from config.settings import BACKTEST_FEE_RATE, BACKTEST_SLIPPAGE_PCT
from utils.logger import get_logger

log = get_logger("pairs_copula")


@dataclass
class CopulaParams:
    formacao: int = 500       # mesma janela de H10 (specs 039/054) -- comparabilidade
    entrada_h: float = 0.05   # h1|2 <= entrada_h dispara entrada (A anormalmente barato dado B)
    saida_h: float = 0.5      # sai quando h1|2 volta para perto do equilibrio (0.5)
    stop_h: float = 0.01      # abandona a tese se h1|2 ficar extremo demais (divergencia)
    max_pares: int = 3


def _cdf_empirica_pontos(base: np.ndarray, novos: np.ndarray) -> np.ndarray:
    """Posicao percentil de `novos` na distribuicao empirica de `base`
    (rank/(n+1), mesma convencao usada para ajustar a copula) -- usa
    `searchsorted` para nao vazar `novos` na propria base de ajuste."""
    ordenado = np.sort(base)
    n = len(ordenado)
    posicoes = np.searchsorted(ordenado, novos, side="left")
    return (posicoes + 0.5) / (n + 1)


def ajustar_copula_gaussiana(retornos_a: np.ndarray, retornos_b: np.ndarray) -> float:
    """Rho da cópula gaussiana -- correlação de Pearson sobre os escores
    normais das marginais transformadas (Sklar), não sobre os retornos
    brutos (que podem ter caudas pesadas que distorceriam Pearson)."""
    ua = _cdf_empirica_pontos(retornos_a, retornos_a)
    ub = _cdf_empirica_pontos(retornos_b, retornos_b)
    za = norm.ppf(np.clip(ua, 1e-6, 1 - 1e-6))
    zb = norm.ppf(np.clip(ub, 1e-6, 1 - 1e-6))
    if za.std() == 0 or zb.std() == 0:
        return 0.0
    rho = float(np.corrcoef(za, zb)[0, 1])
    return max(-0.999, min(0.999, rho))


def h_condicional(u1: float, u2: float, rho: float) -> float:
    """h(u1|u2) = P(U1 <= u1 | U2 = u2) para cópula gaussiana bivariada,
    forma fechada (Eq. 4 de Tadi & Witzany 2025)."""
    z1 = norm.ppf(np.clip(u1, 1e-6, 1 - 1e-6))
    z2 = norm.ppf(np.clip(u2, 1e-6, 1 - 1e-6))
    denom = np.sqrt(max(1e-9, 1 - rho ** 2))
    return float(norm.cdf((z1 - rho * z2) / denom))


def _retornos_log(precos: np.ndarray) -> np.ndarray:
    return np.diff(np.log(precos))


def _h1_dado_2_atual(precos: pd.DataFrame, par: ParCointegrado, i: int, formacao: int):
    """Ajusta a cópula na janela de formação terminando em `i-1` e avalia
    h1|2 no retorno realizado no candle `i` -- ponto-no-tempo, nunca usa
    o candle `i` para ajustar a cópula que o avalia."""
    ini = max(0, i - formacao)
    serie_a = precos[par.a].to_numpy()[ini:i + 1]
    serie_b = precos[par.b].to_numpy()[ini:i + 1]
    if len(serie_a) < 30:
        return None
    ret_a = _retornos_log(serie_a)
    ret_b = _retornos_log(serie_b)
    if len(ret_a) < 20:
        return None
    formacao_a, novo_a = ret_a[:-1], ret_a[-1:]
    formacao_b, novo_b = ret_b[:-1], ret_b[-1:]
    rho = ajustar_copula_gaussiana(formacao_a, formacao_b)
    u1 = float(_cdf_empirica_pontos(formacao_a, novo_a)[0])
    u2 = float(_cdf_empirica_pontos(formacao_b, novo_b)[0])
    return h_condicional(u1, u2, rho)


def run_pairs_copula_backtest(
    dados: Dict[str, pd.DataFrame],
    params: Optional[PairsParams] = None,
    cp: Optional[CopulaParams] = None,
    initial_capital: float = 1000.0,
    fee_rate: float = BACKTEST_FEE_RATE,
    slippage_pct: float = BACKTEST_SLIPPAGE_PCT,
    reselecionar_a_cada: Optional[int] = None,
) -> BacktestResult:
    """Mesma estrutura de `run_pairs_trading.run_pairs_backtest` (long-only,
    mesma restrição declarada em H10 -- chaves spot-only) -- só troca o
    sinal de entrada/saída de z-score linear para h condicional da
    cópula. Seleção de pares (`selecionar_pares`) reusada sem alteração."""
    p = params or PairsParams(formacao=500)
    c = cp or CopulaParams(formacao=p.formacao)
    cadencia = reselecionar_a_cada if reselecionar_a_cada is not None else p.formacao

    series = {}
    for simbolo, df in dados.items():
        if df is None or df.empty or "close" not in df.columns:
            continue
        s = df["close"].copy()
        s.index = pd.to_datetime(df.index)
        series[simbolo] = s
    if len(series) < 2:
        return _resultado_vazio_local(initial_capital)

    precos = pd.concat(series, axis=1, join="inner").dropna()
    if len(precos) <= p.formacao + 10:
        log.warning("historico insuficiente para a janela de formacao")
        return _resultado_vazio_local(initial_capital)

    capital = initial_capital
    abertas: Dict[str, tuple] = {}
    trades: List[Trade] = []
    curva: List[float] = []
    selecionados: List[ParCointegrado] = []

    for i in range(p.formacao, len(precos)):
        linha = precos.iloc[i]
        agora = precos.index[i]
        equity = capital + sum(q * linha[s] for s, (q, *_r) in abertas.items())
        curva.append(equity)

        if (i - p.formacao) % cadencia == 0:
            selecionados = selecionar_pares(precos, p, ate=i)

        if not selecionados:
            continue

        for simbolo in list(abertas.keys()):
            qtd, entrada, custo, taxa_ent, hora_ent, par = abertas[simbolo]
            h = _h1_dado_2_atual(precos, par, i, c.formacao)
            motivo = None
            if h is not None:
                if h >= c.saida_h:
                    motivo = "Reversao concluida"
                elif h <= c.stop_h:
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
            h = _h1_dado_2_atual(precos, par, i, c.formacao)
            if h is None or h > c.entrada_h:
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

    return _montar_local(trades, capital, initial_capital, curva, precos,
                         p.formacao, fee_rate, slippage_pct)


def _montar_local(trades, capital, initial_capital, curva, precos, ini, fee_rate, slippage_pct):
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


def _resultado_vazio_local(initial_capital: float) -> BacktestResult:
    metrics = _calculate_advanced_metrics([])
    return BacktestResult(
        trades=[], initial_capital=initial_capital, final_capital=initial_capital,
        total_return_pct=0.0, win_rate=0.0, total_trades=0, max_drawdown_pct=0.0,
        buy_hold_return_pct=0.0, edge_return_pct=0.0, **metrics,
    )


def run_pairs_copula_scan(
    pares: Optional[List[str]] = None,
    params: Optional[PairsParams] = None,
    cp: Optional[CopulaParams] = None,
    dados: Optional[Dict[str, pd.DataFrame]] = None,
):
    """Split treino/validação idêntico a H10 (`split_treino_validacao`,
    reusado sem alteração) -- mesmo critério de aprovação, sem inventar
    critério novo."""
    from backtesting.approval import evaluate_approval
    from backtesting.pairs_trading import UNIVERSO_AMPLO_HISTORICO_COMPLETO, split_treino_validacao
    from config.settings import TIMEFRAME
    from data.fetcher import fetch_ohlcv

    p = params or PairsParams(formacao=500)
    c = cp or CopulaParams(formacao=p.formacao)
    pares = pares if pares is not None else list(UNIVERSO_AMPLO_HISTORICO_COMPLETO)

    if dados is None:
        dados = {par: fetch_ohlcv(par, TIMEFRAME, 6000) for par in pares}
    dados_treino, dados_validacao = split_treino_validacao(dados, p.formacao)

    resultado_treino = run_pairs_copula_backtest(dados_treino, p, c, reselecionar_a_cada=120)
    resultado_validacao = run_pairs_copula_backtest(dados_validacao, p, c, reselecionar_a_cada=120)
    veredito = evaluate_approval(resultado_validacao)

    return resultado_treino, resultado_validacao, veredito
