import csv

from data.decisions_analysis import analyze_decisions

_HEADERS = [
    "timestamp", "cycle_id", "symbol", "timeframe", "price", "signal",
    "decision", "in_position", "entry_opened", "blockers",
]


def _write_csv(path, rows, headers=_HEADERS):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=headers)
        w.writeheader()
        for row in rows:
            w.writerow({h: row.get(h, "") for h in headers})


def test_analyze_decisions_counts_signals_and_blocked_entries(tmp_path):
    path = tmp_path / "decisions.csv"
    _write_csv(path, [
        {"signal": "BUY", "entry_opened": "True", "blockers": ""},
        {"signal": "BUY", "entry_opened": "False", "blockers": "cooldown"},
        {"signal": "SELL", "entry_opened": "False", "blockers": ""},
        {"signal": "HOLD", "entry_opened": "False", "blockers": ""},
        {"signal": "HOLD", "entry_opened": "False", "blockers": ""},
    ])

    result = analyze_decisions(str(path))

    assert result.status == "ok"
    assert result.total_cycles == 5
    assert result.signal_counts == {"BUY": 2, "SELL": 1, "HOLD": 2}
    assert result.blocked_entries == 1


def test_analyze_decisions_ranks_blockers_by_frequency(tmp_path):
    path = tmp_path / "decisions.csv"
    _write_csv(path, [
        {"signal": "BUY", "entry_opened": "False", "blockers": "cooldown"},
        {"signal": "BUY", "entry_opened": "False", "blockers": "cooldown"},
        {"signal": "BUY", "entry_opened": "False", "blockers": "sem slot"},
        {"signal": "BUY", "entry_opened": "False", "blockers": "cooldown, MTF"},
    ])

    result = analyze_decisions(str(path))

    assert result.blocker_counts[0] == ("cooldown", 3)
    counts = dict(result.blocker_counts)
    assert counts["sem slot"] == 1
    assert counts["MTF"] == 1


def test_analyze_decisions_reports_no_data_when_file_missing(tmp_path):
    missing_path = tmp_path / "nao-existe.csv"

    result = analyze_decisions(str(missing_path))

    assert result.status == "sem_dados"
    assert result.total_cycles == 0
    assert result.signal_counts == {}
    assert result.blocker_counts == []


def test_analyze_decisions_reports_no_data_when_file_empty(tmp_path):
    path = tmp_path / "decisions.csv"
    _write_csv(path, [])

    result = analyze_decisions(str(path))

    assert result.status == "sem_dados"
    assert result.total_cycles == 0


def test_analyze_decisions_tolerates_rows_with_missing_columns(tmp_path):
    # Schema antigo: linha sem a coluna "blockers" (arquivo girado antes dela existir).
    path = tmp_path / "decisions.csv"
    old_headers = ["timestamp", "cycle_id", "symbol", "timeframe", "price", "signal",
                   "decision", "in_position", "entry_opened"]
    _write_csv(path, [
        {"signal": "BUY", "entry_opened": "True"},
        {"signal": "HOLD", "entry_opened": "False"},
    ], headers=old_headers)

    result = analyze_decisions(str(path))

    assert result.status == "ok"
    assert result.total_cycles == 2
    assert result.signal_counts == {"BUY": 1, "HOLD": 1}
    assert result.blocked_entries == 0  # sem coluna blockers, nao pode contar bloqueio
    assert result.blocker_counts == []
