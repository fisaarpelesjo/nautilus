from dataclasses import dataclass
from typing import Callable, Iterable, List

import pandas as pd

from backtesting.engine import simulate_backtest
from config.settings import (
    DYNAMIC_PAIRS_CANDIDATES,
    DYNAMIC_PAIRS_TOP_N,
    BLACKLIST_PAIRS,
    MAX_SPREAD_PCT,
    MIN_VOLATILITY_PCT,
    MIN_VOLUME_USDT,
    TIMEFRAME,
)
from data.fetcher import fetch_ohlcv, get_exchange
from strategy.ema_rsi import EmaRsiStrategy
from utils.logger import get_logger

log = get_logger("market_selector")

STABLECOINS = {"USDC", "BUSD", "TUSD", "USDP", "DAI", "FDUSD", "USDT", "USDS"}


@dataclass
class PairCandidate:
    symbol: str
    volume_24h: float
    spread_pct: float
    volatility_pct: float
    trend_pct: float
    backtest_return_pct: float = 0.0
    backtest_trades: int = 0
    score: float = 0.0


def select_dynamic_pairs(
    tickers: dict | None = None,
    fetch_ohlcv_fn: Callable[[str, str], pd.DataFrame] = fetch_ohlcv,
    timeframe: str = TIMEFRAME,
    top_n: int = DYNAMIC_PAIRS_TOP_N,
    candidate_limit: int = DYNAMIC_PAIRS_CANDIDATES,
    min_volume_usdt: float = MIN_VOLUME_USDT,
    max_spread_pct: float = MAX_SPREAD_PCT,
    min_volatility_pct: float = MIN_VOLATILITY_PCT,
) -> List[PairCandidate]:
    tickers = tickers if tickers is not None else get_exchange().fetch_tickers()
    candidates = _filter_tickers(tickers, min_volume_usdt, max_spread_pct)[:candidate_limit]
    selected: List[PairCandidate] = []

    for candidate in candidates:
        try:
            df = fetch_ohlcv_fn(candidate.symbol, timeframe)
            candidate.volatility_pct = _volatility_pct(df)
            candidate.trend_pct = _trend_pct(df)
            if candidate.volatility_pct < min_volatility_pct or candidate.trend_pct <= 0:
                continue

            strategy = EmaRsiStrategy()
            prepared = strategy.calculate_indicators(df)
            result = simulate_backtest(prepared, strategy)
            candidate.backtest_return_pct = result.total_return_pct
            candidate.backtest_trades = result.total_trades
            candidate.score = _score_candidate(candidate)
            selected.append(candidate)
        except Exception as exc:
            log.error(f"{candidate.symbol}: erro na selecao dinamica: {exc}")

    return sorted(selected, key=lambda item: item.score, reverse=True)[:top_n]


def selected_symbols(candidates: Iterable[PairCandidate]) -> List[str]:
    return [candidate.symbol for candidate in candidates]


def _filter_tickers(tickers: dict, min_volume_usdt: float, max_spread_pct: float) -> List[PairCandidate]:
    candidates = []
    for symbol, ticker in tickers.items():
        if not symbol.endswith("/USDT"):
            continue
        base = symbol.split("/")[0]
        if base in STABLECOINS or is_blacklisted(symbol):
            continue

        volume = float(ticker.get("quoteVolume") or 0)
        bid = float(ticker.get("bid") or 0)
        ask = float(ticker.get("ask") or 0)
        spread = _spread_pct(bid, ask)
        if volume < min_volume_usdt or spread > max_spread_pct:
            continue

        candidates.append(PairCandidate(
            symbol=symbol,
            volume_24h=volume,
            spread_pct=spread,
            volatility_pct=0.0,
            trend_pct=0.0,
        ))

    return sorted(candidates, key=lambda item: item.volume_24h, reverse=True)


def is_blacklisted(symbol: str, blacklist: set[str] | None = None) -> bool:
    blacklist = blacklist if blacklist is not None else BLACKLIST_PAIRS
    normalized = symbol.upper()
    base = normalized.split("/")[0]
    return normalized in blacklist or base in blacklist


def _spread_pct(bid: float, ask: float) -> float:
    mid = (bid + ask) / 2
    return (ask - bid) / mid if bid > 0 and ask > 0 and mid > 0 else 1.0


def _volatility_pct(df: pd.DataFrame, window: int = 20) -> float:
    recent = df.tail(window)
    if recent.empty:
        return 0.0
    return float(((recent["high"] - recent["low"]) / recent["close"]).mean() * 100)


def _trend_pct(df: pd.DataFrame, window: int = 20) -> float:
    recent = df.tail(window)
    if len(recent) < 2:
        return 0.0
    first = float(recent["close"].iloc[0])
    last = float(recent["close"].iloc[-1])
    return (last - first) / first * 100 if first else 0.0


def _score_candidate(candidate: PairCandidate) -> float:
    if candidate.backtest_trades < 2:
        return -9999.0
    volume_score = min(candidate.volume_24h / 100_000_000, 5.0)
    spread_penalty = candidate.spread_pct * 100
    return (
        candidate.backtest_return_pct
        + candidate.trend_pct
        + candidate.volatility_pct / 2
        + volume_score
        - spread_penalty
    )
