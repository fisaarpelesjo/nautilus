from trading import runner


class _FakeManager:
    def __init__(self, balance=5000.0):
        self._balance = balance

    def _reference_balance(self):
        return self._balance


def test_print_live_confirmation_banner_shows_pairs_balance_and_limits(monkeypatch):
    calls = []
    monkeypatch.setattr(runner, "live_confirmation_banner", lambda *args, **kwargs: calls.append((args, kwargs)))
    monkeypatch.setattr(runner, "log_event", lambda *args, **kwargs: None)
    manager = _FakeManager(balance=5000.0)

    runner._print_live_confirmation_banner(["BTC/USDT", "ETH/USDT"], manager)

    assert len(calls) == 1
    args, _kwargs = calls[0]
    pairs, balance, max_order_size, max_positions, daily_pct, weekly_pct, monthly_pct, max_losses = args
    assert pairs == ["BTC/USDT", "ETH/USDT"]
    assert balance == 5000.0
    assert max_order_size > 0
    assert max_positions >= 1
    assert daily_pct > 0
    assert weekly_pct > 0
    assert monthly_pct > 0
    assert max_losses >= 1


def test_print_live_confirmation_banner_logs_live_session_started_event(monkeypatch):
    logged_events = []
    monkeypatch.setattr(runner, "live_confirmation_banner", lambda *args, **kwargs: None)
    monkeypatch.setattr(runner, "log_event", lambda event, **kwargs: logged_events.append((event, kwargs)))
    manager = _FakeManager(balance=1234.5)

    runner._print_live_confirmation_banner(["BTC/USDT"], manager)

    assert len(logged_events) == 1
    event, kwargs = logged_events[0]
    assert event == "live_session_started"
    assert kwargs["balance_usdt"] == 1234.5
    assert kwargs["pairs"] == ["BTC/USDT"]


def test_maybe_print_live_banner_calls_banner_when_live(monkeypatch):
    monkeypatch.setattr(runner, "TRADING_MODE", "live")
    calls = []
    monkeypatch.setattr(runner, "_print_live_confirmation_banner", lambda pairs, manager: calls.append(pairs))
    manager = _FakeManager()

    runner._maybe_print_live_banner(["BTC/USDT"], manager)

    assert calls == [["BTC/USDT"]]


def test_maybe_print_live_banner_skips_when_paper(monkeypatch):
    monkeypatch.setattr(runner, "TRADING_MODE", "paper")
    calls = []
    monkeypatch.setattr(runner, "_print_live_confirmation_banner", lambda pairs, manager: calls.append(pairs))
    manager = _FakeManager()

    runner._maybe_print_live_banner(["BTC/USDT"], manager)

    assert calls == []
