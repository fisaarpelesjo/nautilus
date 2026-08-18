from typing import Iterable, Optional

from config.settings import MAX_POSITION_CORRELATION, CORRELATION_LOOKBACK
from data.fetcher import fetch_ohlcv
from utils.logger import get_logger

log = get_logger("correlation")


def check_correlated_exposure(symbol: str, timeframe: str, open_symbols: Iterable[str]) -> Optional[str]:
    """Retorna o symbol de uma posicao ja aberta com que `symbol` esta altamente
    correlacionado (retornos >= MAX_POSITION_CORRELATION na janela CORRELATION_LOOKBACK),
    ou None se nenhuma correlacao alta for encontrada.

    Falha ABERTA por comparacao (nao bloqueia a entrada so porque o historico de UM
    par ja aberto falhou ao buscar) -- diferente do padrao fail-closed do resto de
    trading/position_lifecycle.py (liquidez, saldo, MTF), porque aqui o dado que falta
    e sobre uma posicao DIFERENTE da que esta sendo avaliada: bloquear toda entrada
    nova por causa de um fetch falho num par nao relacionado seria desproporcional.
    A protecao primaria contra dado desconhecido continua nas outras checagens.
    """
    others = [s for s in open_symbols if s != symbol]
    if not others:
        return None

    try:
        candidate_returns = fetch_ohlcv(symbol, timeframe)["close"].pct_change().dropna().tail(CORRELATION_LOOKBACK)
    except Exception as exc:
        log.warning(f"Falha ao buscar historico de {symbol} para checagem de correlacao: {exc}")
        return None
    if len(candidate_returns) < CORRELATION_LOOKBACK // 2:
        return None

    for other_symbol in others:
        try:
            other_returns = fetch_ohlcv(other_symbol, timeframe)["close"].pct_change().dropna().tail(CORRELATION_LOOKBACK)
        except Exception as exc:
            log.warning(f"Falha ao buscar historico de {other_symbol} para checagem de correlacao: {exc}")
            continue

        aligned_len = min(len(candidate_returns), len(other_returns))
        if aligned_len < CORRELATION_LOOKBACK // 2:
            continue

        corr = candidate_returns.tail(aligned_len).reset_index(drop=True).corr(
            other_returns.tail(aligned_len).reset_index(drop=True)
        )
        if corr is not None and corr >= MAX_POSITION_CORRELATION:
            log.info(f"Correlacao alta: {symbol} x {other_symbol} = {corr:.2f}")
            return other_symbol

    return None
