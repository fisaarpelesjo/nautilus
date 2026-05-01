from data import trade_logger


def test_save_and_load_state_round_trip(tmp_path, monkeypatch):
    state_file = tmp_path / "state.json"
    monkeypatch.setattr(trade_logger, "STATE_FILE", str(state_file))

    state = {
        "paper_balance_usdt": 1234.5,
        "positions": {"BTC/USDT": {"entry_price": 100.0}},
    }

    trade_logger.save_state(state)

    assert trade_logger.load_state() == state


def test_load_state_returns_empty_dict_when_missing(tmp_path, monkeypatch):
    monkeypatch.setattr(trade_logger, "STATE_FILE", str(tmp_path / "missing.json"))

    assert trade_logger.load_state() == {}
