import json
from dataclasses import dataclass

from utils import report_export


@dataclass
class _FakeResult:
    total_trades: int
    total_return_pct: float


def test_export_report_creates_json_csv_and_markdown(tmp_path, monkeypatch):
    monkeypatch.setattr(report_export, "REPORTS_DIR", str(tmp_path / "reports"))

    result = _FakeResult(total_trades=5, total_return_pct=3.2)
    report_export.export_report("backtest", {"symbol": "BTC/USDT", "timeframe": "4h"}, result)

    files = list((tmp_path / "reports").iterdir())
    extensions = {f.suffix for f in files}
    assert extensions == {".json", ".csv", ".md"}

    json_file = next(f for f in files if f.suffix == ".json")
    data = json.loads(json_file.read_text(encoding="utf-8"))
    assert data["params"]["symbol"] == "BTC/USDT"
    assert data["result"]["total_trades"] == 5


def test_export_report_creates_reports_dir_if_missing(tmp_path, monkeypatch):
    reports_dir = tmp_path / "does_not_exist_yet" / "reports"
    monkeypatch.setattr(report_export, "REPORTS_DIR", str(reports_dir))
    assert not reports_dir.exists()

    result = _FakeResult(total_trades=1, total_return_pct=0.5)
    report_export.export_report("scan", {}, result)

    assert reports_dir.exists()
    assert len(list(reports_dir.iterdir())) == 3


def test_export_report_does_not_overwrite_previous_execution(tmp_path, monkeypatch):
    monkeypatch.setattr(report_export, "REPORTS_DIR", str(tmp_path / "reports"))
    result = _FakeResult(total_trades=1, total_return_pct=0.5)

    timestamps = iter(["20260101-000000", "20260101-000001"])
    monkeypatch.setattr(report_export, "_timestamp", lambda: next(timestamps))

    report_export.export_report("backtest", {}, result)
    report_export.export_report("backtest", {}, result)

    json_files = list((tmp_path / "reports").glob("backtest_*.json"))
    assert len(json_files) == 2


def test_export_report_flattens_nested_dict_result_for_csv_and_markdown(tmp_path, monkeypatch):
    # backtest --validate exporta um dict aninhado ({"train": {...}, "validation": {...},
    # "verdict": {...}}) em vez de um dataclass unico -- CSV/Markdown nao podem ficar vazios.
    monkeypatch.setattr(report_export, "REPORTS_DIR", str(tmp_path / "reports"))

    result = {
        "train": {"total_trades": 5, "trades": ["t1", "t2"]},
        "validation": {"total_trades": 2},
        "verdict": {"status": "aprovado"},
    }
    report_export.export_report("backtest_validate", {"symbol": "BTC/USDT"}, result)

    csv_file = next((tmp_path / "reports").glob("*.csv"))
    csv_text = csv_file.read_text(encoding="utf-8")
    assert "train_total_trades" in csv_text
    assert "validation_total_trades" in csv_text
    assert "verdict_status" in csv_text
    assert "train_trades" not in csv_text

    md_file = next((tmp_path / "reports").glob("*.md"))
    md_text = md_file.read_text(encoding="utf-8")
    assert "train_total_trades" in md_text
    assert "verdict_status" in md_text
