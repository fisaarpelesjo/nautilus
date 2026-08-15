from trading import panel
from utils import display


class _FakeManager:
    def __init__(self, positions=None):
        self.positions = positions or {}
        self.paper_balance_usdt = 1000.0
        self.realized_pnl = 0.0


class _FakeSnapshot:
    free_cash = 1000.0
    positions_value = 0.0
    total_equity = 1000.0
    realized_pnl = 0.0
    unrealized_pnl = 0.0
    total_pnl = 0.0
    positions_with_unknown_price = []
    prices = {}


def test_print_panel_with_full_history_shows_all_sections(monkeypatch):
    # Regressao (achado de code-review): panel.py faz `from trading.portfolio
    # import compute_portfolio_snapshot` (import direto, cria binding local)
    # -- so faz efeito fazer monkeypatch no atributo de `trading.panel`, nao
    # no modulo de origem `trading.portfolio`.
    monkeypatch.setattr(panel, "compute_portfolio_snapshot", lambda manager: _FakeSnapshot())
    monkeypatch.setattr(panel, "load_recent_trades", lambda n=10: [
        {"symbol": "BTC/USDT", "exit_reason": "take profit", "pnl_usdt": "5.0", "closed_at": "2026-01-01"},
    ])
    monkeypatch.setattr(panel, "load_recent_signals", lambda n=10: [
        {"symbol": "BTC/USDT", "signal": "BUY", "timestamp": "2026-01-01"},
    ])
    from data.decisions_analysis import DecisionsAnalysisResult
    monkeypatch.setattr(
        panel, "analyze_decisions",
        lambda: DecisionsAnalysisResult(
            status="ok", total_cycles=10, signal_counts={"BUY": 2}, blocked_entries=1,
            blocker_counts=[("cooldown", 1)],
        ),
    )

    printed = []
    monkeypatch.setattr(display.console, "print", lambda *args, **kwargs: printed.append(str(args)))

    panel.print_panel(_FakeManager())

    joined = " ".join(printed)
    assert "1,000.00" in joined or "1000.00" in joined  # patrimonio
    assert "BTC/USDT" in joined  # ultima operacao/sinal
    assert "cooldown" in joined  # bloqueio recente


def test_print_panel_with_no_history_shows_empty_state(monkeypatch):
    monkeypatch.setattr(panel, "compute_portfolio_snapshot", lambda manager: _FakeSnapshot())
    monkeypatch.setattr(panel, "load_recent_trades", lambda n=10: [])
    monkeypatch.setattr(panel, "load_recent_signals", lambda n=10: [])
    from data.decisions_analysis import DecisionsAnalysisResult
    monkeypatch.setattr(panel, "analyze_decisions", lambda: DecisionsAnalysisResult(status="sem_dados"))

    panel.print_panel(_FakeManager())  # nao deve lancar excecao
