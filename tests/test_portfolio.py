from execution.order_manager import Position
from trading import portfolio


class _FakeManager:
    def __init__(self, paper_balance=1000.0, realized_pnl=0.0, positions=None):
        self.paper_balance_usdt = paper_balance
        self.realized_pnl = realized_pnl
        self.positions = positions or {}


def test_snapshot_without_positions_equals_free_cash(monkeypatch):
    monkeypatch.setattr(portfolio, "TRADING_MODE", "paper")
    manager = _FakeManager(paper_balance=1000.0, realized_pnl=50.0)

    snap = portfolio.compute_portfolio_snapshot(manager)

    assert snap.free_cash == 1000.0
    assert snap.positions_value == 0.0
    assert snap.total_equity == 1000.0
    assert snap.realized_pnl == 50.0
    assert snap.unrealized_pnl == 0.0
    assert snap.total_pnl == 50.0
    assert snap.positions_with_unknown_price == []


def test_snapshot_with_open_position_calculates_all_fields(monkeypatch):
    monkeypatch.setattr(portfolio, "TRADING_MODE", "paper")
    monkeypatch.setattr(portfolio, "fetch_ticker", lambda symbol: {"last": 110.0})
    pos = Position(symbol="BTC/USDT", side="long", entry_price=100.0, quantity=2.0, stop_loss=90.0, take_profit=120.0)
    manager = _FakeManager(paper_balance=500.0, realized_pnl=10.0, positions={"BTC/USDT": pos})

    snap = portfolio.compute_portfolio_snapshot(manager)

    assert snap.positions_value == 220.0  # 2.0 * 110.0
    assert snap.total_equity == 720.0  # 500 + 220
    assert snap.unrealized_pnl == 20.0  # (110-100) * 2.0
    assert snap.total_pnl == 30.0  # 10 (realizado) + 20 (nao realizado)
    assert snap.positions_with_unknown_price == []


def test_snapshot_propagates_none_when_price_unavailable(monkeypatch):
    monkeypatch.setattr(portfolio, "TRADING_MODE", "paper")
    monkeypatch.setattr(portfolio, "fetch_ticker", lambda symbol: (_ for _ in ()).throw(RuntimeError("timeout")))
    pos = Position(symbol="BTC/USDT", side="long", entry_price=100.0, quantity=2.0, stop_loss=90.0, take_profit=120.0)
    manager = _FakeManager(paper_balance=500.0, realized_pnl=10.0, positions={"BTC/USDT": pos})

    snap = portfolio.compute_portfolio_snapshot(manager)

    assert snap.positions_value is None
    assert snap.total_equity is None
    assert snap.unrealized_pnl is None
    assert snap.total_pnl is None
    assert snap.positions_with_unknown_price == ["BTC/USDT"]
    assert snap.free_cash == 500.0  # caixa livre continua conhecida


def test_snapshot_mixes_known_and_unknown_prices(monkeypatch):
    monkeypatch.setattr(portfolio, "TRADING_MODE", "paper")

    def _fetch_ticker(symbol):
        if symbol == "BTC/USDT":
            return {"last": 110.0}
        raise RuntimeError("timeout")

    monkeypatch.setattr(portfolio, "fetch_ticker", _fetch_ticker)
    positions = {
        "BTC/USDT": Position(symbol="BTC/USDT", side="long", entry_price=100.0, quantity=1.0, stop_loss=90.0, take_profit=120.0),
        "ETH/USDT": Position(symbol="ETH/USDT", side="long", entry_price=50.0, quantity=1.0, stop_loss=45.0, take_profit=60.0),
    }
    manager = _FakeManager(paper_balance=100.0, realized_pnl=0.0, positions=positions)

    snap = portfolio.compute_portfolio_snapshot(manager)

    assert snap.positions_value is None
    assert snap.positions_with_unknown_price == ["ETH/USDT"]
