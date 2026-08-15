import main
from trading import portfolio
from utils import display


class _FakeSnapshot:
    def __init__(self):
        self.free_cash = 500.0
        self.positions_value = 220.0
        self.total_equity = 720.0
        self.realized_pnl = 10.0
        self.unrealized_pnl = 20.0
        self.total_pnl = 30.0
        self.positions_with_unknown_price = []


def test_cmd_status_uses_portfolio_snapshot(monkeypatch):
    from execution import order_manager
    monkeypatch.setattr(order_manager, "TRADING_MODE", "paper")
    monkeypatch.setattr(order_manager, "load_state", lambda: {})
    monkeypatch.setattr("data.killswitch_store.load_killswitch", lambda: False)

    captured = {"manager": None}

    def _fake_snapshot(manager):
        captured["manager"] = manager
        return _FakeSnapshot()

    monkeypatch.setattr(portfolio, "compute_portfolio_snapshot", _fake_snapshot)

    printed = []
    monkeypatch.setattr(display.console, "print", lambda *args, **kwargs: printed.append(str(args)))

    main.cmd_status()

    assert captured["manager"] is not None
    joined = " ".join(printed)
    assert "500.00" in joined  # caixa livre
    assert "720.00" in joined  # patrimonio total
    assert "20.00" in joined  # pnl nao realizado
