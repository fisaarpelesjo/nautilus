import csv
import dataclasses
import json
from datetime import datetime
from pathlib import Path
from typing import Optional

REPORTS_DIR = "reports"


def _timestamp() -> str:
    return datetime.now().strftime("%Y%m%d-%H%M%S")


def _to_plain_dict(obj) -> dict:
    if dataclasses.is_dataclass(obj):
        return dataclasses.asdict(obj)
    if isinstance(obj, dict):
        return obj
    return {"value": obj}


def export_report(name: str, params: dict, result, ranking: Optional[list] = None) -> None:
    """Salva o resultado de uma execucao (backtest/scan/multibacktest/optimize)
    em reports/ nos formatos JSON, CSV e Markdown -- historico auditavel entre
    execucoes (ROADMAP.md Fase 1 item 4). Reusa dataclasses.asdict() sobre o
    resultado ja existente em vez de um schema de relatorio paralelo."""
    Path(REPORTS_DIR).mkdir(parents=True, exist_ok=True)
    timestamp = _timestamp()
    base_path = Path(REPORTS_DIR) / f"{name}_{timestamp}"

    result_dict = _to_plain_dict(result)
    ranking_dict = [_to_plain_dict(r) for r in ranking] if ranking else None
    payload = {"name": name, "timestamp": timestamp, "params": params, "result": result_dict}
    if ranking_dict is not None:
        payload["ranking"] = ranking_dict

    with open(f"{base_path}.json", "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, default=str, ensure_ascii=False)

    _write_csv(f"{base_path}.csv", params, result_dict)
    _write_markdown(f"{base_path}.md", name, timestamp, params, result_dict, ranking_dict)


def _flatten_scalars(d: dict, prefix: str = "") -> dict:
    """So campos escalares -- listas complexas (ex: BacktestResult.trades) ja
    estao completas no JSON, nao fazem sentido achatadas numa unica linha de
    CSV. Dicts aninhados (ex: {"train": {...}, "validation": {...}} de
    `backtest --validate`) sao achatados um nivel com prefixo em vez de
    descartados, senao a linha de CSV/Markdown fica vazia."""
    flat = {}
    for k, v in d.items():
        key = f"{prefix}{k}"
        if isinstance(v, dict):
            flat.update(_flatten_scalars(v, prefix=f"{key}_"))
        elif not isinstance(v, list):
            flat[key] = v
    return flat


def _write_csv(path: str, params: dict, result_dict: dict) -> None:
    row = {**{f"param_{k}": v for k, v in params.items()}, **_flatten_scalars(result_dict)}
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(row.keys()))
        writer.writeheader()
        writer.writerow(row)


def _write_markdown(path: str, name: str, timestamp: str, params: dict, result_dict: dict, ranking_dict) -> None:
    lines = [f"# Relatorio: {name}", "", f"Executado em: {timestamp}", "", "## Parametros", ""]
    for k, v in params.items():
        lines.append(f"- **{k}**: {v}")
    lines += ["", "## Resultado", ""]
    for k, v in _flatten_scalars(result_dict).items():
        lines.append(f"- **{k}**: {v}")
    if ranking_dict:
        lines += ["", "## Ranking", ""]
        for i, item in enumerate(ranking_dict, start=1):
            lines.append(f"{i}. {item}")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
