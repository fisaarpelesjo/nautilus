import csv
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Tuple

from rich import box
from rich.table import Table

from data.paths import DECISIONS_FILE
from utils.display import C_DIM, C_LABEL, C_NEG, C_POS, console, header


@dataclass
class DecisionRecord:
    signal: str
    entry_opened: bool
    blockers: List[str] = field(default_factory=list)


@dataclass
class DecisionsAnalysisResult:
    status: str  # "ok" | "sem_dados"
    total_cycles: int = 0
    signal_counts: Dict[str, int] = field(default_factory=dict)
    blocked_entries: int = 0
    blocker_counts: List[Tuple[str, int]] = field(default_factory=list)


def analyze_decisions(path: str = DECISIONS_FILE) -> DecisionsAnalysisResult:
    records = _load_decisions(path)
    if not records:
        return DecisionsAnalysisResult(status="sem_dados")

    signal_counts: Dict[str, int] = defaultdict(int)
    blocker_counter: Counter = Counter()
    blocked_entries = 0

    for record in records:
        if record.signal:
            signal_counts[record.signal] += 1
        if record.blockers:
            blocked_entries += 1
            blocker_counter.update(record.blockers)

    return DecisionsAnalysisResult(
        status="ok",
        total_cycles=len(records),
        signal_counts=dict(signal_counts),
        blocked_entries=blocked_entries,
        blocker_counts=blocker_counter.most_common(),
    )


def print_decisions_analysis(result: DecisionsAnalysisResult):
    header()
    console.print(f"  [{C_LABEL}]analise de decisoes[/{C_LABEL}]")
    console.print()

    if result.status == "sem_dados":
        console.print(
            f"  [{C_DIM}]nenhum dado para analisar ainda -- rode o bot para gerar "
            f"{DECISIONS_FILE}[/{C_DIM}]"
        )
        console.print()
        return

    console.print(
        f"  [{C_LABEL}]ciclos[/{C_LABEL}] [white]{result.total_cycles}[/white]"
        f"   [{C_LABEL}]entradas bloqueadas[/{C_LABEL}] "
        f"[{C_NEG if result.blocked_entries else C_POS}]{result.blocked_entries}[/]"
    )
    console.print()

    _print_signal_table(result)
    _print_blocker_table(result)


def run(path: str = DECISIONS_FILE):
    print_decisions_analysis(analyze_decisions(path))


def _load_decisions(path: str) -> List[DecisionRecord]:
    if not Path(path).exists():
        return []

    with open(path, newline="", encoding="utf-8") as f:
        rows = csv.DictReader(f)
        records = []
        for row in rows:
            signal = (row.get("signal") or "").strip()
            entry_opened = (row.get("entry_opened") or "").strip().lower() == "true"
            raw_blockers = row.get("blockers")
            blockers = (
                [b.strip() for b in raw_blockers.split(",") if b.strip()]
                if raw_blockers else []
            )
            records.append(DecisionRecord(signal=signal, entry_opened=entry_opened, blockers=blockers))
        return records


def _print_signal_table(result: DecisionsAnalysisResult):
    table = Table(box=box.SIMPLE, show_header=True, header_style="bold dim", border_style="dim", pad_edge=False)
    table.add_column("  sinal", style="white", min_width=10)
    table.add_column("ciclos", justify="right", min_width=8)

    for signal, count in sorted(result.signal_counts.items(), key=lambda item: item[1], reverse=True):
        table.add_row(f"  {signal}", str(count))

    console.print(table)
    console.print()


def _print_blocker_table(result: DecisionsAnalysisResult):
    if not result.blocker_counts:
        console.print(f"  [{C_DIM}]nenhum bloqueio registrado[/{C_DIM}]")
        console.print()
        return

    table = Table(box=box.SIMPLE, show_header=True, header_style="bold dim", border_style="dim", pad_edge=False)
    table.add_column("  bloqueio mais frequente", style="white", min_width=24)
    table.add_column("ocorrencias", justify="right", min_width=12)

    for blocker, count in result.blocker_counts:
        table.add_row(f"  {blocker}", str(count))

    console.print(table)
    console.print()
