"""H25 -- sazonalidade por sessao de negociacao (hora do dia UTC).
`specs/062-h25-sazonalidade-horaria/research.md` declara antes de medir:

D1 (janelas): tres blocos de 8h UTC, pre-registrados por convencao de mercado
(sessao asiatica, europeia, americana) -- nao escolhidos apos olhar resultado.
"Filtro" significa RESTRINGIR novas entradas a dentro da janela -- mesma
framing de H5 (bloquear, nao favorecer), e mesmo escopo dos filtros aditivos
ja existentes (REGIME_FILTER_ENABLED/HIGH_VOLATILITY_FILTER_ENABLED): so
novas entradas (BUY), nunca a saida (SELL) de uma posicao ja aberta.

D2 (universo): UNIVERSO_H11 (12 pares, backtesting/horizonte.py) -- ja
estabelecido, nao escolhido para este teste.

D3 (disciplina estatistica -- o que impede repetir a armadilha de H5): H5
reprovou por "so na busca" (passou na janela de descoberta, nao sustentou
fora). Aqui, os TRES blocos x 12 pares (36 combinacoes) sao TODOS reportados
(pre-registrados, sem selecao post-hoc de qual bloco olhar) e cada combinacao
passa pela MESMA bateria de confirmacao fora da amostra que H10/H14/H20 ja
usam (backtesting.multimarket.classify -- confirmado/so_na_busca/reprovado/
inconclusivo). So "confirmado" conta como evidencia real.
"""
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import pandas as pd

from backtesting.engine import BacktestResult, Signal, precompute_signals, simulate_backtest
from backtesting.horizonte import UNIVERSO_H11
from backtesting.multimarket import classify
from backtesting.validation import split_train_validation
from data.fetcher import fetch_ohlcv
from strategy.ema_rsi import EmaRsiStrategy

TIMEFRAME = "4h"

# D1: tres blocos de 8h UTC, convencao de mercado -- declarados antes de medir.
JANELAS: Dict[str, Tuple[int, int]] = {
    "asia": (0, 8),
    "europa": (8, 16),
    "eua": (16, 24),
}


def filtrar_por_sessao(sinais: pd.Series, inicio: int, fim: int) -> pd.Series:
    """Mascara BUY fora de [inicio, fim) horas UTC para HOLD. SELL nunca e
    tocado -- uma posicao ja aberta sempre pode sair, mesmo escopo de
    REGIME_FILTER_ENABLED/HIGH_VOLATILITY_FILTER_ENABLED (ema_rsi.py)."""
    hora = sinais.index.hour
    dentro_da_janela = (hora >= inicio) & (hora < fim)
    resultado = sinais.copy()
    bloqueia = (sinais == Signal.BUY) & ~dentro_da_janela
    resultado[bloqueia] = Signal.HOLD
    return resultado


@dataclass
class ResultadoSazonalidadePar:
    par: str
    janela_nome: str
    pf_busca_base: Optional[float]
    pf_busca_filtrado: Optional[float]
    status: str  # confirmado / defensivo / so_na_busca / reprovado / inconclusivo / erro
    search_result: Optional[BacktestResult] = None
    confirmation_result: Optional[BacktestResult] = None
    erro: Optional[str] = None


def _avaliar_par_janela(par: str, janela_nome: str, inicio: int, fim: int,
                         candle_limit: int = 2000,
                         initial_capital: float = 1000.0) -> ResultadoSazonalidadePar:
    estrategia = EmaRsiStrategy()
    try:
        df = fetch_ohlcv(par, TIMEFRAME, limit=candle_limit)
        df = estrategia.calculate_indicators(df)
    except Exception as exc:
        return ResultadoSazonalidadePar(par=par, janela_nome=janela_nome,
                                         pf_busca_base=None, pf_busca_filtrado=None,
                                         status="erro", erro=str(exc)[:120])

    # Sinais sobre o df INTEIRO antes do split -- mesmo motivo ja documentado
    # em multimarket.py/validation.py: por fatia, o shift(1) do cruzamento de
    # EMA perderia contexto no primeiro candle da janela de confirmacao.
    sinais_base = precompute_signals(df, estrategia)
    sinais_filtrados = filtrar_por_sessao(sinais_base, inicio, fim)

    search_df, confirmation_df = split_train_validation(df)

    search_base = simulate_backtest(
        search_df, estrategia, initial_capital=initial_capital,
        precomputed_signals=sinais_base.loc[search_df.index],
    )
    search_filtrado = simulate_backtest(
        search_df, estrategia, initial_capital=initial_capital,
        precomputed_signals=sinais_filtrados.loc[search_df.index],
    )

    confirmation_filtrado = None
    if confirmation_df is not None:
        confirmation_filtrado = simulate_backtest(
            confirmation_df, estrategia, initial_capital=initial_capital, start_index=0,
            precomputed_signals=sinais_filtrados.loc[confirmation_df.index],
        )

    return ResultadoSazonalidadePar(
        par=par, janela_nome=janela_nome,
        pf_busca_base=search_base.profit_factor,
        pf_busca_filtrado=search_filtrado.profit_factor,
        status=classify(search_filtrado, confirmation_filtrado),
        search_result=search_filtrado,
        confirmation_result=confirmation_filtrado,
    )


def avaliar_sazonalidade(pares: Optional[List[str]] = None,
                          janelas: Optional[Dict[str, Tuple[int, int]]] = None,
                          ) -> List[ResultadoSazonalidadePar]:
    pares = list(pares) if pares is not None else list(UNIVERSO_H11)
    janelas = janelas if janelas is not None else JANELAS

    resultados = []
    for janela_nome, (inicio, fim) in janelas.items():
        for par in pares:
            resultados.append(_avaliar_par_janela(par, janela_nome, inicio, fim))
    return resultados
