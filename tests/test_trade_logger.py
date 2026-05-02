from data import decision_store, state_store


def test_save_and_load_state_round_trip(tmp_path, monkeypatch):
    state_file = tmp_path / "state.json"
    monkeypatch.setattr(state_store, "STATE_FILE", str(state_file))

    state = {
        "paper_balance_usdt": 1234.5,
        "positions": {"BTC/USDT": {"entry_price": 100.0}},
    }

    state_store.save_state(state)

    assert state_store.load_state() == state


def test_load_state_returns_empty_dict_when_missing(tmp_path, monkeypatch):
    monkeypatch.setattr(state_store, "STATE_FILE", str(tmp_path / "missing.json"))

    assert state_store.load_state() == {}


def test_log_decision_writes_analysis_row(tmp_path, monkeypatch):
    decisions_file = tmp_path / "decisions.csv"
    monkeypatch.setattr(decision_store, "DECISIONS_FILE", str(decisions_file))

    decision_store.log_decision({
        "timestamp": "2026-01-01T00:00:00",
        "cycle_id": 1,
        "symbol": "BTC/USDT",
        "timeframe": "4h",
        "signal": "HOLD",
        "decision": "aguardando: sem cruzamento/pullback",
        "volume_ratio": 0.8,
        "pullback_entry": False,
    })

    content = decisions_file.read_text(encoding="utf-8")

    assert "cycle_id,symbol,timeframe" in content
    assert "BTC/USDT" in content
    assert "sem cruzamento/pullback" in content
