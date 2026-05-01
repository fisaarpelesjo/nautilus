import json

from utils import logger


def test_log_event_writes_jsonl(tmp_path, monkeypatch):
    monkeypatch.setattr(logger, "LOG_DIR", str(tmp_path))

    logger.log_event("test_event", symbol="BTC/USDT", pnl=1.23)

    files = list(tmp_path.glob("events-*.jsonl"))
    assert len(files) == 1

    payload = json.loads(files[0].read_text(encoding="utf-8").strip())
    assert payload["event"] == "test_event"
    assert payload["symbol"] == "BTC/USDT"
    assert payload["pnl"] == 1.23
    assert "timestamp" in payload
