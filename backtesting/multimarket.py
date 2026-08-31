"""Varredura de estrategia x simbolo com confirmacao fora da amostra (spec 023).

O problema que este modulo resolve nao e "avaliar varios mercados" -- isso
backtesting/compare.py ja faria. E que **testar muitas combinacoes produz
aprovacoes por acaso**: com o profit factor mediano observado neste projeto
(0,60), e matematicamente esperado que algumas combinacoes passem por sorte
numa varredura de N estrategias x M simbolos.

O guarda-corpo: uma combinacao so e "confirmada" se passar tambem numa janela
de dados que NAO participou da sua descoberta. Reusa
backtesting/validation.py::split_train_validation() e
backtesting/approval.py::evaluate_approval() -- nenhum criterio de aprovacao
novo e inventado aqui (decisao D3 de research.md).
"""
from dataclasses import dataclass, field
from typing import List, Optional

from backtesting.approval import evaluate_approval
from backtesting.engine import BacktestResult, precompute_signals, simulate_backtest
from backtesting.validation import split_train_validation
from data.fetcher import fetch_ohlcv
from data.markets import require_cost, resolve_market
from utils.logger import get_logger

log = get_logger("multimarket")

# Ordem de qualidade dos status. Um resultado confirmado com numero modesto vale
# mais que um espetacular que so passou onde foi descoberto -- o segundo e
# exatamente o que a varredura existe para nao vender como descoberta.
# "defensivo" fica acima de "so_na_busca" porque prova edge de verdade NA
# PROPRIA janela de confirmacao (PF/drawdown/trades passam) -- so_na_busca nao
# prova nada fora da amostra, so repete o que a busca ja mostrou.
_ORDEM_STATUS = {"confirmado": 0, "defensivo": 1, "so_na_busca": 2, "reprovado": 3, "inconclusivo": 4, "erro": 5}


def classify(search: Optional[BacktestResult], confirmation: Optional[BacktestResult]) -> str:
    """Status de uma combinacao a partir das duas janelas.

    `confirmation is None` significa que o historico nao deu para dividir --
    inconclusivo, jamais aprovado por omissao de dado (FR-012).
    """
    if search is None:
        return "erro"
    if confirmation is None:
        return "inconclusivo"

    aprovado_na_confirmacao = evaluate_approval(confirmation).status == "aprovado"
    if aprovado_na_confirmacao:
        return "confirmado"

    # Passou onde foi descoberto mas nao se sustentou fora: MUST NOT ser
    # apresentado como aprovado (FR-014).
    if evaluate_approval(search).status == "aprovado":
        return "so_na_busca"

    # Perfil defensivo (achado real na varredura de spec de pesquisa de
    # estrategias, 2026-08-31): teria sido aprovado na confirmacao nao fosse
    # por nao bater um buy-and-hold de rali extremo (visto ate +400% em
    # alguns pares no periodo) -- PF, drawdown e volume de trades ja provam
    # edge real out-of-sample. O bot nunca aloca 100% num unico par, entao
    # "bater buy-and-hold" e uma regua mais severa que o risco que o bot de
    # fato assume. Distinto de "confirmado": MUST NOT ser tratado como
    # aprovacao (mesmo espirito do guard-corpo de FR-014 acima) -- so separa
    # "sem edge" de "edge real que nao venceu manter o ativo comprado".
    if evaluate_approval(confirmation, require_beat_buy_hold=False).status == "aprovado":
        return "defensivo"

    return "reprovado"


@dataclass
class ScanEntry:
    strategy_name: str
    symbol: str
    market: Optional[str]
    search_result: Optional[BacktestResult]
    confirmation_result: Optional[BacktestResult]
    status: str
    error: Optional[str] = None
    cost_profile_note: Optional[str] = None
    has_session_gaps: bool = False


@dataclass
class MultiMarketScanResult:
    combinations_tested: int = 0
    entries: List[ScanEntry] = field(default_factory=list)

    def add(self, entry: ScanEntry) -> None:
        self.entries.append(entry)
        self.combinations_tested += 1

    def ranked(self) -> List[ScanEntry]:
        """Ordena por qualidade do status primeiro, retorno da confirmacao depois.

        O status domina de proposito: ordenar por retorno faria a combinacao
        espetacular-mas-nao-confirmada aparecer no topo, que e precisamente a
        leitura errada que este modulo existe para impedir.
        """
        def chave(e: ScanEntry):
            ret = e.confirmation_result.total_return_pct if e.confirmation_result else float("-inf")
            return (_ORDEM_STATUS.get(e.status, 9), -ret)

        return sorted(self.entries, key=chave)


def run_scan(strategies: dict, symbols: List[str], timeframe: str = "4h",
             candle_limit: int = 2000, initial_capital: float = 1000.0) -> MultiMarketScanResult:
    """Avalia cada estrategia contra cada simbolo, com confirmacao fora da amostra.

    Um simbolo que falha ao buscar dados vira entrada de erro e NAO interrompe
    os demais -- uma varredura de 40 simbolos que morre no terceiro e inutil.
    """
    resultado = MultiMarketScanResult()

    for nome, estrategia in strategies.items():
        for symbol in symbols:
            try:
                resultado.add(_avaliar(nome, estrategia, symbol, timeframe, candle_limit, initial_capital))
            except Exception as exc:
                log.warning(f"{nome} x {symbol}: {exc}")
                resultado.add(ScanEntry(
                    strategy_name=nome, symbol=symbol, market=None,
                    search_result=None, confirmation_result=None,
                    status="erro", error=str(exc)[:120],
                ))

    return resultado


def _avaliar(nome: str, estrategia, symbol: str, timeframe: str,
             candle_limit: int, initial_capital: float) -> ScanEntry:
    market = resolve_market(symbol)
    cost = require_cost(market)

    df = fetch_ohlcv(symbol, timeframe, limit=candle_limit)
    df = estrategia.calculate_indicators(df)

    # Sinais calculados sobre o df INTEIRO antes do split, pelo mesmo motivo
    # documentado em backtesting/validation.py: calculados por fatia, o shift(1)
    # do cruzamento de EMA perderia contexto no primeiro candle da janela de
    # confirmacao e descartaria um cruzamento real na fronteira.
    signals = precompute_signals(df, estrategia) if hasattr(estrategia, "params") else None

    search_df, confirmation_df = split_train_validation(df)

    search = simulate_backtest(
        search_df, estrategia, initial_capital=initial_capital,
        fee_rate=cost.fee_rate, slippage_pct=cost.slippage_pct,
        precomputed_signals=signals.loc[search_df.index] if signals is not None else None,
    )

    confirmation = None
    if confirmation_df is not None:
        confirmation = simulate_backtest(
            confirmation_df, estrategia, initial_capital=initial_capital,
            start_index=0, fee_rate=cost.fee_rate, slippage_pct=cost.slippage_pct,
            precomputed_signals=signals.loc[confirmation_df.index] if signals is not None else None,
        )

    return ScanEntry(
        strategy_name=nome, symbol=symbol, market=market.name,
        search_result=search, confirmation_result=confirmation,
        status=classify(search, confirmation),
        cost_profile_note=cost.source_note,
        has_session_gaps=not market.continuous,
    )
