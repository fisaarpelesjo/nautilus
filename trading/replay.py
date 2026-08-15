from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import List, Optional

from data.fetcher import fetch_ohlcv
from execution import order_manager
from execution.order_manager import OrderManager
from strategy.ema_rsi import EmaRsiStrategy
from trading.position_lifecycle import handle_entry_candidate, handle_open_position

START_INDEX = 100


@dataclass
class ReplayResult:
    symbol: str
    timeframe: str
    trades: List[dict] = field(default_factory=list)
    total_trades: int = 0
    total_pnl: float = 0.0
    blocked_cycles: int = 0


@dataclass
class ReplayComparison:
    replay_trades: int
    backtest_trades: int
    replay_return_pct: float
    backtest_return_pct: float
    notes: List[str] = field(default_factory=list)


def compare_to_backtest(result: ReplayResult, backtest_result, initial_capital: float = 1000.0) -> ReplayComparison:
    """Compara o resultado do replay (caminho de decisao real) contra um
    backtest simples do mesmo par/periodo -- reusa run_backtest() ja
    existente (spec 006), nao duplica simulacao. Notas fixas explicam
    divergencias conhecidas, nunca inventam diferenca onde nao ha."""
    replay_return_pct = (result.total_pnl / initial_capital * 100) if initial_capital else 0.0
    backtest_return_pct = backtest_result.total_return_pct

    notes: List[str] = []
    if result.total_trades == backtest_result.total_trades:
        notes.append("Sem divergencia no numero de trades entre replay e backtest.")
    elif result.total_trades < backtest_result.total_trades:
        notes.append(
            f"Replay teve menos trades ({result.total_trades}) que o backtest "
            f"({backtest_result.total_trades}) -- cooldown/MTF/circuit breaker do caminho real "
            "podem ter bloqueado entradas que o backtest simplificado nao modela."
        )
    else:
        notes.append(
            f"Replay teve mais trades ({result.total_trades}) que o backtest "
            f"({backtest_result.total_trades}) -- verificar se algum filtro esta desabilitado "
            "no replay mas habilitado nos parametros usados pelo backtest."
        )

    notes.append(
        "Limitacoes conhecidas: cooldown do replay usa relogio real (nao o timestamp do candle "
        "historico) e MTF busca o timeframe de confirmacao mais recente disponivel, nao "
        "point-in-time -- ver research.md da spec 008."
    )

    return ReplayComparison(
        replay_trades=result.total_trades,
        backtest_trades=backtest_result.total_trades,
        replay_return_pct=replay_return_pct,
        backtest_return_pct=backtest_return_pct,
        notes=notes,
    )


@contextmanager
def _isolated_order_manager_environment():
    """Isola OrderManager de todo I/O real durante um replay -- MUST nunca
    tocar data/state.json/data/trades.csv/logs reais nem enviar Telegram
    real, mesmo em erro (constitution Principle I). Mesmo padrao ja usado
    extensivamente pela suite de testes deste projeto
    (monkeypatch.setattr(order_manager, ...)), aplicado aqui via
    try/finally fora do contexto de teste -- restaura sempre, inclusive em
    excecao. TRADING_MODE forcado "paper" garante que OrderManager nunca
    entra no caminho _live_buy/_live_sell, independente do .env real."""
    collected_trades: List[dict] = []
    originals = {
        "TRADING_MODE": order_manager.TRADING_MODE,
        "load_state": order_manager.load_state,
        "save_state": order_manager.save_state,
        "log_trade": order_manager.log_trade,
        "log_event": order_manager.log_event,
        "send_telegram": order_manager.send_telegram,
    }
    order_manager.TRADING_MODE = "paper"
    order_manager.load_state = lambda: {}
    order_manager.save_state = lambda state: None
    order_manager.log_trade = lambda trade: collected_trades.append(trade)
    order_manager.log_event = lambda *args, **kwargs: None
    order_manager.send_telegram = lambda msg: None
    try:
        yield collected_trades
    finally:
        for name, value in originals.items():
            setattr(order_manager, name, value)


def run_replay(symbol: str, timeframe: Optional[str] = None, candle_limit: int = 2000) -> ReplayResult:
    """Roda o caminho de decisao real (handle_entry_candidate/
    handle_open_position, os mesmos usados pelo loop de producao) candle a
    candle sobre historico publico -- nao a simulacao simplificada de
    backtesting/engine.py. Isolado (ver _isolated_order_manager_environment):
    nunca toca os arquivos reais do bot, nunca envia ordem real."""
    from config.settings import TIMEFRAME as DEFAULT_TIMEFRAME
    timeframe = timeframe or DEFAULT_TIMEFRAME

    df = fetch_ohlcv(symbol, timeframe, limit=candle_limit)
    strategy = EmaRsiStrategy()
    blocked_cycles = 0

    with _isolated_order_manager_environment() as collected_trades:
        manager = OrderManager()
        trade_events: list = []

        for i in range(START_INDEX, len(df)):
            window = df.iloc[:i + 1]
            signal = strategy.generate_signal(window)
            prepared = strategy.calculate_indicators(window)
            if len(prepared) < 2:
                continue

            indicators = prepared.iloc[-1]
            current_price = float(signal.price)
            row: dict = {}
            pos = manager.get_position(symbol)

            if pos:
                handle_open_position(manager, symbol, pos, signal, current_price, row, trade_events)
            else:
                handle_entry_candidate(
                    manager, symbol, signal, indicators, current_price, strategy,
                    row, trade_events, new_entries=0, max_entries_per_cycle=1,
                    killswitch_active=False,
                )
                if row.get("blockers"):
                    blocked_cycles += 1

    total_pnl = sum(float(t.get("pnl_usdt") or 0.0) for t in collected_trades)
    return ReplayResult(
        symbol=symbol, timeframe=timeframe, trades=collected_trades,
        total_trades=len(collected_trades), total_pnl=total_pnl, blocked_cycles=blocked_cycles,
    )
