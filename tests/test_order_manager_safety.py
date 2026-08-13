import pytest

from execution import order_manager
from execution.order_manager import LIVE_CONFIRMATION_TEXT, OrderManager
from risk.manager import RiskLevels


def test_order_manager_does_not_initialize_exchange_in_paper(monkeypatch):
    monkeypatch.setattr(order_manager, "TRADING_MODE", "paper")
    monkeypatch.setattr(order_manager, "load_state", lambda: {})
    monkeypatch.setattr(
        order_manager,
        "get_exchange",
        lambda: pytest.fail("paper mode must not initialize live exchange"),
    )

    manager = OrderManager()

    assert manager.exchange is None


def test_live_mode_requires_explicit_confirmation(monkeypatch):
    monkeypatch.setattr(order_manager, "TRADING_MODE", "live")
    monkeypatch.setattr(order_manager, "LIVE_TRADING_CONFIRMATION", "")
    monkeypatch.setattr(order_manager, "BINANCE_API_KEY", "key")
    monkeypatch.setattr(order_manager, "BINANCE_API_SECRET", "secret")
    monkeypatch.setattr(order_manager, "load_state", lambda: {})

    with pytest.raises(RuntimeError, match="Live trading bloqueado"):
        OrderManager()


def test_live_mode_requires_api_credentials(monkeypatch):
    monkeypatch.setattr(order_manager, "TRADING_MODE", "live")
    monkeypatch.setattr(order_manager, "LIVE_TRADING_CONFIRMATION", LIVE_CONFIRMATION_TEXT)
    monkeypatch.setattr(order_manager, "BINANCE_API_KEY", "")
    monkeypatch.setattr(order_manager, "BINANCE_API_SECRET", "")
    monkeypatch.setattr(order_manager, "load_state", lambda: {})

    with pytest.raises(RuntimeError, match="BINANCE_API_KEY"):
        OrderManager()


def test_generate_client_order_id_is_unique():
    ids = {order_manager._generate_client_order_id() for _ in range(200)}

    assert len(ids) == 200


def _paper_manager(monkeypatch, logged_trades=None):
    monkeypatch.setattr(order_manager, "TRADING_MODE", "paper")
    monkeypatch.setattr(order_manager, "load_state", lambda: {})
    monkeypatch.setattr(order_manager, "save_state", lambda state: None)
    monkeypatch.setattr(order_manager, "send_telegram", lambda msg: None)
    if logged_trades is not None:
        monkeypatch.setattr(order_manager, "log_trade", lambda trade: logged_trades.append(trade))
    return OrderManager()


def test_paper_buy_assigns_unique_client_order_id(monkeypatch):
    manager = _paper_manager(monkeypatch)
    risk = RiskLevels(entry_price=100.0, stop_loss=95.0, take_profit=110.0, quantity=1.0, risk_usdt=5.0)

    manager.open_long("BTC/USDT", risk)

    pos = manager.get_position("BTC/USDT")
    assert pos.client_order_id
    assert pos.client_order_id.startswith("bot-")


def test_paper_sell_persists_client_order_id_on_trade(monkeypatch):
    logged_trades = []
    manager = _paper_manager(monkeypatch, logged_trades)
    risk = RiskLevels(entry_price=100.0, stop_loss=95.0, take_profit=110.0, quantity=1.0, risk_usdt=5.0)
    manager.open_long("BTC/USDT", risk)
    client_order_id = manager.get_position("BTC/USDT").client_order_id

    manager.close_position("BTC/USDT", "take_profit", current_price=110.0)

    assert logged_trades[0]["client_order_id"] == client_order_id


def test_paper_sell_removes_position_even_if_log_trade_fails(monkeypatch):
    # Regressao: contadores (total_trades, realized_pnl, daily_pnl) sao
    # incrementados antes do log_trade/log_event/telegram. Se essa ordem
    # ficasse invertida (posicao removida so depois de logar) e log_trade
    # falhasse, a posicao ficaria presa e o proximo ciclo contaria o mesmo
    # trade de novo, inflando os contadores.
    manager = _paper_manager(monkeypatch)
    monkeypatch.setattr(
        order_manager, "log_trade",
        lambda trade: (_ for _ in ()).throw(OSError("trades.csv sem espaco")),
    )
    risk = RiskLevels(entry_price=100.0, stop_loss=95.0, take_profit=110.0, quantity=1.0, risk_usdt=5.0)
    manager.open_long("BTC/USDT", risk)

    manager.close_position("BTC/USDT", "take_profit", current_price=110.0)

    assert not manager.has_position("BTC/USDT")
    assert manager.total_trades == 1

    # Uma segunda tentativa de fechar (ex: proximo ciclo re-avaliando o mesmo
    # symbol) nao deve fazer nada, pois a posicao ja nao existe mais.
    manager.close_position("BTC/USDT", "take_profit", current_price=110.0)
    assert manager.total_trades == 1


def test_record_reconciliation_persists_and_is_restored(monkeypatch):
    saved_states = []
    monkeypatch.setattr(order_manager, "TRADING_MODE", "paper")
    monkeypatch.setattr(order_manager, "load_state", lambda: {})
    monkeypatch.setattr(order_manager, "save_state", lambda state: saved_states.append(state))

    manager = OrderManager()
    manager.record_reconciliation("mismatch", "2026-08-13T00:00:00", ["BTC/USDT: divergente"])

    assert manager.last_reconciliation["status"] == "mismatch"
    assert saved_states[-1]["last_reconciliation"]["status"] == "mismatch"

    monkeypatch.setattr(order_manager, "load_state", lambda: saved_states[-1])
    restored = OrderManager()
    assert restored.last_reconciliation["status"] == "mismatch"


def test_live_sell_keeps_local_position_when_exchange_call_fails(monkeypatch):
    class _FailingExchange:
        def create_market_sell_order(self, symbol, quantity, params=None):
            raise RuntimeError("network timeout")

    monkeypatch.setattr(order_manager, "TRADING_MODE", "live")
    monkeypatch.setattr(order_manager, "LIVE_TRADING_CONFIRMATION", LIVE_CONFIRMATION_TEXT)
    monkeypatch.setattr(order_manager, "BINANCE_API_KEY", "key")
    monkeypatch.setattr(order_manager, "BINANCE_API_SECRET", "secret")
    monkeypatch.setattr(order_manager, "load_state", lambda: {})
    monkeypatch.setattr(order_manager, "save_state", lambda state: None)
    monkeypatch.setattr(order_manager, "send_telegram", lambda msg: None)
    monkeypatch.setattr(order_manager, "get_exchange", lambda: _FailingExchange())

    manager = OrderManager()
    manager.positions["BTC/USDT"] = order_manager.Position(
        symbol="BTC/USDT", side="long", entry_price=100.0, quantity=1.0,
        stop_loss=95.0, take_profit=110.0,
    )

    manager.close_position("BTC/USDT", "stop_loss")

    assert manager.has_position("BTC/USDT")


def test_persist_state_with_retry_succeeds_on_second_attempt(monkeypatch):
    calls = []

    def _flaky_save_state(state):
        calls.append(state)
        if len(calls) == 1:
            raise OSError("disk busy")

    monkeypatch.setattr(order_manager, "TRADING_MODE", "paper")
    monkeypatch.setattr(order_manager, "load_state", lambda: {})
    monkeypatch.setattr(order_manager, "save_state", _flaky_save_state)

    manager = OrderManager()
    manager._persist_state_with_retry("teste")

    assert len(calls) == 2


def test_persist_state_with_retry_gives_up_after_all_attempts(monkeypatch, caplog):
    monkeypatch.setattr(order_manager, "TRADING_MODE", "paper")
    monkeypatch.setattr(order_manager, "load_state", lambda: {})

    def _always_fails(state):
        raise OSError("disk full")

    monkeypatch.setattr(order_manager, "save_state", _always_fails)

    manager = OrderManager()
    manager._persist_state_with_retry("teste")  # nao deve levantar


def test_live_sell_does_not_abort_when_first_persist_fails(monkeypatch):
    calls = []

    class _SucceedingExchange:
        def create_market_sell_order(self, symbol, quantity, params=None):
            calls.append(params.get("newClientOrderId"))
            return {"id": "abc123", "average": 100.0}

    monkeypatch.setattr(order_manager, "TRADING_MODE", "live")
    monkeypatch.setattr(order_manager, "LIVE_TRADING_CONFIRMATION", LIVE_CONFIRMATION_TEXT)
    monkeypatch.setattr(order_manager, "BINANCE_API_KEY", "key")
    monkeypatch.setattr(order_manager, "BINANCE_API_SECRET", "secret")
    monkeypatch.setattr(order_manager, "load_state", lambda: {})
    monkeypatch.setattr(order_manager, "save_state", lambda state: (_ for _ in ()).throw(OSError("disk busy")))
    monkeypatch.setattr(order_manager, "send_telegram", lambda msg: None)
    monkeypatch.setattr(order_manager, "get_exchange", lambda: _SucceedingExchange())
    monkeypatch.setattr(order_manager, "log_trade", lambda trade: None)

    manager = OrderManager()
    manager.positions["BTC/USDT"] = order_manager.Position(
        symbol="BTC/USDT", side="long", entry_price=100.0, quantity=1.0,
        stop_loss=95.0, take_profit=110.0,
    )

    manager.close_position("BTC/USDT", "stop_loss")  # nao deve levantar

    assert len(calls) == 1
    assert not manager.has_position("BTC/USDT")


def test_live_sell_reuses_client_order_id_across_retries(monkeypatch):
    calls = []

    class _FailingExchange:
        def create_market_sell_order(self, symbol, quantity, params=None):
            calls.append(params.get("newClientOrderId"))
            raise RuntimeError("network timeout")

    monkeypatch.setattr(order_manager, "TRADING_MODE", "live")
    monkeypatch.setattr(order_manager, "LIVE_TRADING_CONFIRMATION", LIVE_CONFIRMATION_TEXT)
    monkeypatch.setattr(order_manager, "BINANCE_API_KEY", "key")
    monkeypatch.setattr(order_manager, "BINANCE_API_SECRET", "secret")
    monkeypatch.setattr(order_manager, "load_state", lambda: {})
    monkeypatch.setattr(order_manager, "save_state", lambda state: None)
    monkeypatch.setattr(order_manager, "send_telegram", lambda msg: None)
    monkeypatch.setattr(order_manager, "get_exchange", lambda: _FailingExchange())

    manager = OrderManager()
    manager.positions["BTC/USDT"] = order_manager.Position(
        symbol="BTC/USDT", side="long", entry_price=100.0, quantity=1.0,
        stop_loss=95.0, take_profit=110.0,
    )

    manager.close_position("BTC/USDT", "stop_loss")
    manager.close_position("BTC/USDT", "stop_loss")

    assert len(calls) == 2
    assert calls[0] is not None
    assert calls[0] == calls[1]


def test_live_sell_updates_pnl_and_trade_counters(monkeypatch):
    class _SucceedingExchange:
        def create_market_sell_order(self, symbol, quantity, params=None):
            return {"id": "abc123", "average": 90.0}

    logged_trades = []
    monkeypatch.setattr(order_manager, "TRADING_MODE", "live")
    monkeypatch.setattr(order_manager, "LIVE_TRADING_CONFIRMATION", LIVE_CONFIRMATION_TEXT)
    monkeypatch.setattr(order_manager, "BINANCE_API_KEY", "key")
    monkeypatch.setattr(order_manager, "BINANCE_API_SECRET", "secret")
    monkeypatch.setattr(order_manager, "load_state", lambda: {})
    monkeypatch.setattr(order_manager, "save_state", lambda state: None)
    monkeypatch.setattr(order_manager, "send_telegram", lambda msg: None)
    monkeypatch.setattr(order_manager, "get_exchange", lambda: _SucceedingExchange())
    monkeypatch.setattr(order_manager, "log_trade", lambda trade: logged_trades.append(trade))

    manager = OrderManager()
    manager.positions["BTC/USDT"] = order_manager.Position(
        symbol="BTC/USDT", side="long", entry_price=100.0, quantity=1.0,
        stop_loss=90.0, take_profit=110.0,
    )

    manager.close_position("BTC/USDT", "Stop Loss", current_price=90.0)

    # entrada 100, saida 90 (do fill da ordem), qty 1 -> prejuizo de 10
    assert manager.total_trades == 1
    assert manager.winning_trades == 0
    assert manager.realized_pnl == -10.0
    assert manager.daily_pnl == -10.0
    assert logged_trades[0]["pnl_usdt"] == -10.0
    assert logged_trades[0]["exit_price"] == 90.0


def test_live_sell_falls_back_to_current_price_when_order_has_no_fill_price(monkeypatch):
    class _SucceedingExchangeNoFillPrice:
        def create_market_sell_order(self, symbol, quantity, params=None):
            return {"id": "abc123"}  # sem "average"/"price"

    logged_trades = []
    monkeypatch.setattr(order_manager, "TRADING_MODE", "live")
    monkeypatch.setattr(order_manager, "LIVE_TRADING_CONFIRMATION", LIVE_CONFIRMATION_TEXT)
    monkeypatch.setattr(order_manager, "BINANCE_API_KEY", "key")
    monkeypatch.setattr(order_manager, "BINANCE_API_SECRET", "secret")
    monkeypatch.setattr(order_manager, "load_state", lambda: {})
    monkeypatch.setattr(order_manager, "save_state", lambda state: None)
    monkeypatch.setattr(order_manager, "send_telegram", lambda msg: None)
    monkeypatch.setattr(order_manager, "get_exchange", lambda: _SucceedingExchangeNoFillPrice())
    monkeypatch.setattr(order_manager, "log_trade", lambda trade: logged_trades.append(trade))

    manager = OrderManager()
    manager.positions["BTC/USDT"] = order_manager.Position(
        symbol="BTC/USDT", side="long", entry_price=100.0, quantity=1.0,
        stop_loss=90.0, take_profit=110.0,
    )

    manager.close_position("BTC/USDT", "Take Profit", current_price=115.0)

    assert logged_trades[0]["exit_price"] == 115.0
    assert logged_trades[0]["pnl_usdt"] == 15.0


def test_live_sell_removes_position_even_if_post_success_logging_fails(monkeypatch):
    class _SucceedingExchange:
        def create_market_sell_order(self, symbol, quantity, params=None):
            return {"id": "abc123"}

    sent_messages = []
    monkeypatch.setattr(order_manager, "TRADING_MODE", "live")
    monkeypatch.setattr(order_manager, "LIVE_TRADING_CONFIRMATION", LIVE_CONFIRMATION_TEXT)
    monkeypatch.setattr(order_manager, "BINANCE_API_KEY", "key")
    monkeypatch.setattr(order_manager, "BINANCE_API_SECRET", "secret")
    monkeypatch.setattr(order_manager, "load_state", lambda: {})
    monkeypatch.setattr(order_manager, "save_state", lambda state: None)
    monkeypatch.setattr(order_manager, "send_telegram", lambda msg: sent_messages.append(msg))
    monkeypatch.setattr(order_manager, "get_exchange", lambda: _SucceedingExchange())
    monkeypatch.setattr(order_manager, "log_trade", lambda trade: None)
    monkeypatch.setattr(
        order_manager, "log_event",
        lambda *args, **kwargs: (_ for _ in ()).throw(OSError("disk full")),
    )

    manager = OrderManager()
    manager.positions["BTC/USDT"] = order_manager.Position(
        symbol="BTC/USDT", side="long", entry_price=100.0, quantity=1.0,
        stop_loss=95.0, take_profit=110.0,
    )

    manager.close_position("BTC/USDT", "stop_loss")

    assert not manager.has_position("BTC/USDT")
    assert not any("ERRO ao vender" in m for m in sent_messages)
    # log_event falhou (isolado no seu proprio try/except), mas isso nao pode
    # impedir o alerta de telegram de rodar -- sao acoes independentes.
    assert any("VENDA BTC/USDT" in m for m in sent_messages)


def test_live_sell_log_trade_failure_does_not_block_event_and_alert(monkeypatch):
    class _SucceedingExchange:
        def create_market_sell_order(self, symbol, quantity, params=None):
            return {"id": "abc123", "average": 90.0}

    sent_messages = []
    logged_events = []
    monkeypatch.setattr(order_manager, "TRADING_MODE", "live")
    monkeypatch.setattr(order_manager, "LIVE_TRADING_CONFIRMATION", LIVE_CONFIRMATION_TEXT)
    monkeypatch.setattr(order_manager, "BINANCE_API_KEY", "key")
    monkeypatch.setattr(order_manager, "BINANCE_API_SECRET", "secret")
    monkeypatch.setattr(order_manager, "load_state", lambda: {})
    monkeypatch.setattr(order_manager, "save_state", lambda state: None)
    monkeypatch.setattr(order_manager, "send_telegram", lambda msg: sent_messages.append(msg))
    monkeypatch.setattr(order_manager, "get_exchange", lambda: _SucceedingExchange())
    monkeypatch.setattr(
        order_manager, "log_trade",
        lambda trade: (_ for _ in ()).throw(OSError("trades.csv sem espaco")),
    )
    monkeypatch.setattr(order_manager, "log_event", lambda event, **kwargs: logged_events.append(event))

    manager = OrderManager()
    manager.positions["BTC/USDT"] = order_manager.Position(
        symbol="BTC/USDT", side="long", entry_price=100.0, quantity=1.0,
        stop_loss=95.0, take_profit=110.0,
    )

    manager.close_position("BTC/USDT", "stop_loss")

    assert not manager.has_position("BTC/USDT")
    assert "live_order_closed" in logged_events
    assert any("VENDA BTC/USDT" in m for m in sent_messages)
