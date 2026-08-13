from trading import runner


class _FailingExchange:
    def fetch_balance(self):
        raise RuntimeError("API indisponivel")


class _MismatchExchange:
    def fetch_balance(self):
        return {"total": {"BTC": 0.0}}


class _FakePosition:
    def __init__(self, quantity):
        self.quantity = quantity


class _FakeManager:
    def __init__(self, exchange, positions=None, record_raises=False):
        self.exchange = exchange
        self.positions = positions or {}
        self.recorded = []
        self._record_raises = record_raises

    def record_reconciliation(self, status, checked_at, diffs):
        self.recorded.append((status, checked_at, diffs))
        if self._record_raises:
            raise OSError("disk busy")


def test_run_reconciliation_records_error_status_when_reconcile_raises(monkeypatch):
    monkeypatch.setattr(runner, "send_telegram", lambda msg: None)
    manager = _FakeManager(exchange=_FailingExchange())

    runner._run_reconciliation(manager, ["BTC/USDT"])

    assert len(manager.recorded) == 1
    status, _checked_at, diffs = manager.recorded[0]
    assert status == "error"
    assert "API indisponivel" in diffs[0]


def test_run_reconciliation_alerts_on_mismatch(monkeypatch):
    sent_messages = []
    monkeypatch.setattr(runner, "send_telegram", lambda msg: sent_messages.append(msg))
    manager = _FakeManager(
        exchange=_MismatchExchange(),
        positions={"BTC/USDT": _FakePosition(1.0)},
    )

    runner._run_reconciliation(manager, ["BTC/USDT"])

    assert len(manager.recorded) == 1
    status, _checked_at, diffs = manager.recorded[0]
    assert status == "mismatch"
    assert diffs
    assert len(sent_messages) == 1
    assert "Divergencia" in sent_messages[0]


def test_run_reconciliation_still_alerts_when_persisting_result_fails(monkeypatch):
    # Regressao: o alerta de uma divergencia real nao pode ser engolido so
    # porque a persistencia do resultado (record_reconciliation) falhou.
    sent_messages = []
    monkeypatch.setattr(runner, "send_telegram", lambda msg: sent_messages.append(msg))
    manager = _FakeManager(
        exchange=_MismatchExchange(),
        positions={"BTC/USDT": _FakePosition(1.0)},
        record_raises=True,
    )

    runner._run_reconciliation(manager, ["BTC/USDT"])  # nao deve levantar

    assert len(sent_messages) == 1
    assert "Divergencia" in sent_messages[0]
