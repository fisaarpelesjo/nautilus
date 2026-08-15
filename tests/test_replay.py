import pandas as pd
import pytest

from execution import order_manager
from trading import replay


def test_isolated_environment_restores_originals_on_normal_exit():
    original_load_state = order_manager.load_state
    original_save_state = order_manager.save_state
    original_log_trade = order_manager.log_trade
    original_log_event = order_manager.log_event
    original_send_telegram = order_manager.send_telegram
    original_mode = order_manager.TRADING_MODE

    with replay._isolated_order_manager_environment():
        assert order_manager.TRADING_MODE == "paper"
        assert order_manager.load_state is not original_load_state

    assert order_manager.load_state is original_load_state
    assert order_manager.save_state is original_save_state
    assert order_manager.log_trade is original_log_trade
    assert order_manager.log_event is original_log_event
    assert order_manager.send_telegram is original_send_telegram
    assert order_manager.TRADING_MODE == original_mode


def test_isolated_environment_restores_originals_even_on_exception():
    original_load_state = order_manager.load_state
    original_mode = order_manager.TRADING_MODE

    with pytest.raises(RuntimeError):
        with replay._isolated_order_manager_environment():
            assert order_manager.TRADING_MODE == "paper"
            raise RuntimeError("erro simulado dentro do replay")

    assert order_manager.load_state is original_load_state
    assert order_manager.TRADING_MODE == original_mode


def test_isolated_environment_never_calls_real_io_functions(monkeypatch):
    def _fail_load_state():
        pytest.fail("load_state REAL foi chamado dentro do isolamento")

    def _fail_save_state(state):
        pytest.fail("save_state REAL foi chamado dentro do isolamento")

    def _fail_log_trade(trade):
        pytest.fail("log_trade REAL foi chamado dentro do isolamento")

    def _fail_log_event(event, **kwargs):
        pytest.fail("log_event REAL foi chamado dentro do isolamento")

    def _fail_send_telegram(msg):
        pytest.fail("send_telegram REAL foi chamado dentro do isolamento")

    # monkeypatch nos MESMOS nomes que o context manager tambem vai trocar --
    # como o context manager guarda o "original" no momento em que entra,
    # esses sentinelas viram o "original" guardado, e SO retornam quando o
    # context manager sair (restaurando-os) -- dentro do bloco, quem roda e
    # a versao isolada, nunca estas sentinelas.
    monkeypatch.setattr(order_manager, "load_state", _fail_load_state)
    monkeypatch.setattr(order_manager, "save_state", _fail_save_state)
    monkeypatch.setattr(order_manager, "log_trade", _fail_log_trade)
    monkeypatch.setattr(order_manager, "log_event", _fail_log_event)
    monkeypatch.setattr(order_manager, "send_telegram", _fail_send_telegram)

    with replay._isolated_order_manager_environment():
        manager = order_manager.OrderManager()
        risk = _risk()
        manager.open_long("BTC/USDT", risk)
        manager.close_position("BTC/USDT", "take_profit", current_price=110.0)
        # se qualquer uma das sentinelas acima tivesse sido chamada, o
        # pytest.fail() ja teria interrompido o teste antes de chegar aqui.


def test_isolated_environment_forces_paper_mode_regardless_of_real_config(monkeypatch):
    monkeypatch.setattr(order_manager, "TRADING_MODE", "live")

    with replay._isolated_order_manager_environment():
        manager = order_manager.OrderManager()
        assert manager.exchange is None  # nunca inicializa exchange live
        risk = _risk()
        manager.open_long("BTC/USDT", risk)
        assert manager.has_position("BTC/USDT")  # usou _paper_buy, nao _live_buy


def _risk():
    from risk.manager import RiskLevels
    return RiskLevels(entry_price=100.0, stop_loss=95.0, take_profit=110.0, quantity=1.0, risk_usdt=5.0)


def _synthetic_ohlcv(n=200):
    closes = [100.0 + (i % 30) * 0.5 - (i // 30) * 0.2 for i in range(n)]
    return pd.DataFrame({
        "open": closes, "high": [c + 1.0 for c in closes], "low": [c - 1.0 for c in closes],
        "close": closes, "volume": [1000.0] * n,
    }, index=pd.date_range("2024-01-01", periods=n, freq="4h"))


def test_run_replay_calls_real_decision_functions(monkeypatch):
    calls = {"entry": 0, "open_position": 0}
    original_entry = replay.handle_entry_candidate
    original_open = replay.handle_open_position

    def _spy_entry(*args, **kwargs):
        calls["entry"] += 1
        return original_entry(*args, **kwargs)

    def _spy_open(*args, **kwargs):
        calls["open_position"] += 1
        return original_open(*args, **kwargs)

    monkeypatch.setattr(replay, "handle_entry_candidate", _spy_entry)
    monkeypatch.setattr(replay, "handle_open_position", _spy_open)
    monkeypatch.setattr(replay, "fetch_ohlcv", lambda symbol, timeframe, limit=2000: _synthetic_ohlcv())

    result = replay.run_replay("BTC/USDT", "4h")

    assert calls["entry"] > 0
    assert result.symbol == "BTC/USDT"


def test_run_replay_produces_coherent_result_without_network(monkeypatch):
    monkeypatch.setattr(replay, "fetch_ohlcv", lambda symbol, timeframe, limit=2000: _synthetic_ohlcv())

    result = replay.run_replay("BTC/USDT", "4h")

    assert result.total_trades == len(result.trades)
    for trade in result.trades:
        assert "entry_price" in trade
        assert "exit_price" in trade
        assert "pnl_usdt" in trade
