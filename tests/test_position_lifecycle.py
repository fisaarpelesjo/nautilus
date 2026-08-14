from strategy.base import Signal
from trading import position_lifecycle


class _FakePosition:
    def __init__(self, entry_price=100.0, stop_loss=95.0, take_profit=110.0, atr=0.0, highest_price=100.0):
        self.entry_price = entry_price
        self.stop_loss = stop_loss
        self.take_profit = take_profit
        self.atr = atr
        self.highest_price = highest_price
        self.quantity = 1.0


class _FakeSignal:
    def __init__(self, signal=Signal.HOLD):
        self.signal = signal


class _FakeManager:
    def __init__(self, close_succeeds=True, persist_raises=False):
        self._close_succeeds = close_succeeds
        self._persist_raises = persist_raises
        self.positions = {"BTC/USDT": None}
        self.paper_balance_usdt = 1000.0
        self.cooldown_calls = []
        self.close_calls = []
        self.persist_calls = 0

    def close_position(self, symbol, reason, price):
        self.close_calls.append((symbol, reason, price))
        if self._close_succeeds:
            del self.positions[symbol]

    def has_position(self, symbol):
        return symbol in self.positions

    def set_cooldown(self, symbol):
        self.cooldown_calls.append(symbol)

    def _persist_state(self):
        pass

    def _persist_state_with_retry(self, context, attempts=2):
        # Espelha o comportamento real: nunca levanta, so registra a tentativa.
        self.persist_calls += 1
        if self._persist_raises:
            return  # simula "falhou mas foi engolido", como o metodo real faz


class _FakeEntryManager:
    def __init__(self, balance=1000.0, daily_limit_hit=False, in_cooldown=False, open_succeeds=True):
        self.positions = {}
        self.paper_balance_usdt = balance
        self._daily_limit_hit = daily_limit_hit
        self._in_cooldown = in_cooldown
        self._open_succeeds = open_succeeds
        self.open_calls = []

    def is_daily_limit_hit(self):
        return self._daily_limit_hit

    def is_in_cooldown(self, symbol):
        return self._in_cooldown

    def open_long(self, symbol, risk):
        self.open_calls.append((symbol, risk))
        if self._open_succeeds:
            self.positions[symbol] = object()

    def has_position(self, symbol):
        return symbol in self.positions


def test_handle_entry_candidate_blocks_when_balance_unknown(monkeypatch):
    # Regressao: saldo desconhecido nao pode virar 0.0 silenciosamente --
    # isso mandaria uma ordem de quantidade zero de verdade para a exchange.
    monkeypatch.setattr(position_lifecycle, "TRADING_MODE", "live")
    monkeypatch.setattr(
        position_lifecycle, "fetch_balance",
        lambda: (_ for _ in ()).throw(RuntimeError("timeout")),
    )
    # MTF roda antes do saldo (mesma ordem de antes desta spec); mocka para
    # nao bater na rede de verdade no teste.
    monkeypatch.setattr(
        position_lifecycle, "fetch_ohlcv",
        lambda symbol, timeframe: (_ for _ in ()).throw(RuntimeError("sem rede no teste")),
    )
    manager = _FakeEntryManager()
    row = {}
    trade_events = []

    opened = position_lifecycle.handle_entry_candidate(
        manager, "BTC/USDT", _FakeSignal(Signal.BUY), {"atr": 1.0}, 100.0,
        strategy=None, row=row, trade_events=trade_events,
        new_entries=0, max_entries_per_cycle=1,
    )

    assert opened is False
    assert manager.open_calls == []
    assert "saldo indisponivel" in row["blockers"]


def test_handle_entry_candidate_opens_when_balance_known(monkeypatch):
    monkeypatch.setattr(
        position_lifecycle, "fetch_ohlcv",
        lambda symbol, timeframe: (_ for _ in ()).throw(RuntimeError("sem rede no teste")),
    )
    manager = _FakeEntryManager(balance=1000.0)
    row = {}
    trade_events = []

    opened = position_lifecycle.handle_entry_candidate(
        manager, "BTC/USDT", _FakeSignal(Signal.BUY), {"atr": 1.0}, 100.0,
        strategy=None, row=row, trade_events=trade_events,
        new_entries=0, max_entries_per_cycle=1,
    )

    assert opened is True
    assert len(manager.open_calls) == 1


def test_handle_entry_candidate_skips_balance_fetch_when_mtf_blocks(monkeypatch):
    # Regressao: o saldo (chamada de rede) so deve ser buscado se nenhum
    # bloqueio mais barato -- incluindo o MTF, tambem uma chamada de rede --
    # ja tiver descartado a entrada. Buscar o saldo antes do MTF gastaria uma
    # chamada extra sempre que o MTF bloqueasse.
    monkeypatch.setattr(position_lifecycle, "TRADING_MODE", "live")

    class _RealMtfStrategy:
        def calculate_indicators(self, df):
            raise AssertionError("nao deveria chegar aqui neste teste")

    balance_calls = []

    def _fake_ohlcv(symbol, timeframe):
        import pandas as pd
        return pd.DataFrame({"close": [100.0]})

    def _fake_fetch_balance():
        balance_calls.append(1)
        return {"USDT": 1000.0}

    monkeypatch.setattr(position_lifecycle, "fetch_ohlcv", _fake_ohlcv)
    monkeypatch.setattr(position_lifecycle, "fetch_balance", _fake_fetch_balance)

    class _BlockingStrategy:
        def calculate_indicators(self, df):
            return df.assign(ema_trend=[10_000.0])  # preco atual (100) nunca supera isso -> MTF nega

    manager = _FakeEntryManager(balance=1000.0)
    row = {}
    trade_events = []

    opened = position_lifecycle.handle_entry_candidate(
        manager, "BTC/USDT", _FakeSignal(Signal.BUY), {"atr": 1.0}, 100.0,
        strategy=_BlockingStrategy(), row=row, trade_events=trade_events,
        new_entries=0, max_entries_per_cycle=1,
    )

    assert opened is False
    assert "MTF negado" in row["blockers"]
    assert balance_calls == []  # saldo nunca foi buscado


def test_attempt_close_uses_real_balance_in_live_mode(monkeypatch):
    monkeypatch.setattr(position_lifecycle, "TRADING_MODE", "live")
    monkeypatch.setattr(position_lifecycle, "fetch_balance", lambda: {"USDT": 4242.0})
    manager = _FakeManager(close_succeeds=True)
    manager.paper_balance_usdt = 1000.0  # nao deve ser usado em modo live
    pos = _FakePosition(stop_loss=99.0)
    row = {}
    trade_events = []

    position_lifecycle.handle_open_position(manager, "BTC/USDT", pos, _FakeSignal(), 98.0, row, trade_events)

    balance_after = trade_events[0][4]
    assert balance_after == 4242.0


def test_attempt_close_reports_unknown_balance_as_none_on_fetch_failure(monkeypatch):
    # Regressao: saldo desconhecido (falha de rede) nao pode virar "$0.00" --
    # isso pareceria uma conta zerada de verdade para o operador.
    monkeypatch.setattr(position_lifecycle, "TRADING_MODE", "live")

    def _failing_fetch_balance():
        raise RuntimeError("timeout")

    monkeypatch.setattr(position_lifecycle, "fetch_balance", _failing_fetch_balance)
    manager = _FakeManager(close_succeeds=True)
    pos = _FakePosition(stop_loss=99.0)
    row = {}
    trade_events = []

    position_lifecycle.handle_open_position(manager, "BTC/USDT", pos, _FakeSignal(), 98.0, row, trade_events)

    assert trade_events[0][4] is None


def test_handle_open_position_trailing_stop_uses_persist_with_retry():
    manager = _FakeManager(persist_raises=True)
    pos = _FakePosition(entry_price=100.0, stop_loss=90.0, take_profit=200.0, atr=2.0, highest_price=100.0)
    row = {}
    trade_events = []

    # preco sobe o suficiente para o novo trailing stop (108 - 1.5*2=105) ficar
    # acima do stop atual (90), disparando o ajuste, mas sem bater SL nem TP
    position_lifecycle.handle_open_position(manager, "BTC/USDT", pos, _FakeSignal(), 108.0, row, trade_events)

    assert manager.persist_calls == 1  # nao levantou, mesmo com persist_raises=True
    assert row["decision"] == "trailing stop ajustado"
    assert pos.stop_loss == 105.0


def test_handle_open_position_reports_close_on_stop_loss_success():
    manager = _FakeManager(close_succeeds=True)
    pos = _FakePosition(stop_loss=99.0)
    row = {}
    trade_events = []

    position_lifecycle.handle_open_position(manager, "BTC/USDT", pos, _FakeSignal(), 98.0, row, trade_events)

    assert row["decision"] == "fechou: stop loss"
    assert row["in_pos"] is False
    assert len(trade_events) == 1
    assert manager.cooldown_calls == ["BTC/USDT"]


def test_handle_open_position_keeps_position_when_close_silently_fails():
    manager = _FakeManager(close_succeeds=False)
    pos = _FakePosition(stop_loss=99.0)
    row = {"in_pos": True}
    trade_events = []

    position_lifecycle.handle_open_position(manager, "BTC/USDT", pos, _FakeSignal(), 98.0, row, trade_events)

    assert row["decision"] == "fechamento falhou: stop loss (posicao mantida para nova tentativa)"
    assert row["in_pos"] is True
    assert trade_events == []
    assert manager.cooldown_calls == []


def test_handle_open_position_take_profit_does_not_report_close_when_close_fails():
    manager = _FakeManager(close_succeeds=False)
    pos = _FakePosition(take_profit=105.0)
    row = {"in_pos": True}
    trade_events = []

    position_lifecycle.handle_open_position(manager, "BTC/USDT", pos, _FakeSignal(), 106.0, row, trade_events)

    assert row["decision"] == "fechamento falhou: take profit (posicao mantida para nova tentativa)"
    assert trade_events == []


def test_handle_open_position_sell_signal_does_not_report_close_when_close_fails():
    manager = _FakeManager(close_succeeds=False)
    pos = _FakePosition(entry_price=100.0, stop_loss=90.0, take_profit=120.0)
    row = {"in_pos": True}
    trade_events = []

    position_lifecycle.handle_open_position(manager, "BTC/USDT", pos, _FakeSignal(Signal.SELL), 105.0, row, trade_events)

    assert row["decision"] == "fechamento falhou: sinal de venda (posicao mantida para nova tentativa)"
    assert trade_events == []
    assert manager.cooldown_calls == []
