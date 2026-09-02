"""Store de observacoes de H15 -- arbitragem entre corretoras (spec 029).

Persistencia por acrescimo (D5): cada `Comparacao` gerada num ciclo vira uma
linha em `ARBITRAGEM_FILE` (JSONL). Nao usa `data/atomic_io.py::atomic_write`
-- esse padrao reescreve o arquivo inteiro a cada chamada, o oposto do que a
amostra de H15 precisa (acumular entre execucoes, nunca perder a anterior).
Uma execucao interrompida no meio deixa no maximo uma linha parcial no fim,
que `carregar_observacoes()` descarta sem abortar a leitura das demais.
"""

import json
from dataclasses import asdict
from pathlib import Path
from typing import TYPE_CHECKING

from data import paths

if TYPE_CHECKING:
    from backtesting.arbitragem import Comparacao


def registrar_observacoes(comparacoes: list["Comparacao"]) -> None:
    if not comparacoes:
        return
    caminho = Path(paths.ARBITRAGEM_FILE)
    caminho.parent.mkdir(parents=True, exist_ok=True)
    with open(caminho, "a", encoding="utf-8") as f:
        for c in comparacoes:
            f.write(json.dumps(asdict(c), default=str, ensure_ascii=False) + "\n")


def carregar_observacoes() -> list[dict]:
    caminho = Path(paths.ARBITRAGEM_FILE)
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
                # Linha parcial de uma execucao interrompida no meio da
                # escrita (D5) -- descartada, sem abortar a leitura do resto.
                continue
    return observacoes
