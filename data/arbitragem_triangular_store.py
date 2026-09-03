"""Store de observacoes de H22 -- arbitragem triangular intra-corretora
(spec 060). Mesmo padrao de persistencia por acrescimo de
data/arbitragem_store.py (H15, spec 029): cada `CicloTriangular` vira uma
linha em `ARBITRAGEM_TRIANGULAR_FILE` (JSONL), nunca reescreve o arquivo
inteiro."""

import json
from dataclasses import asdict
from pathlib import Path
from typing import TYPE_CHECKING

from data import paths

if TYPE_CHECKING:
    from backtesting.arbitragem_triangular import CicloTriangular


def registrar_ciclos(ciclos: list["CicloTriangular"]) -> None:
    if not ciclos:
        return
    caminho = Path(paths.ARBITRAGEM_TRIANGULAR_FILE)
    caminho.parent.mkdir(parents=True, exist_ok=True)
    with open(caminho, "a", encoding="utf-8") as f:
        for c in ciclos:
            f.write(json.dumps(asdict(c), default=str, ensure_ascii=False) + "\n")


def carregar_observacoes() -> list[dict]:
    caminho = Path(paths.ARBITRAGEM_TRIANGULAR_FILE)
    if not caminho.exists():
        return []
    observacoes = []
    with open(caminho, encoding="utf-8") as f:
        for linha in f:
            linha = linha.strip()
            if not linha:
                continue
            try:
                observacoes.append(json.loads(linha))
            except json.JSONDecodeError:
                continue
    return observacoes
