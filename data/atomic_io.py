import os
from typing import Callable, TextIO


def atomic_write(path: str, write_fn: Callable[[TextIO], None]):
    """Escreve em um arquivo temporario e troca com os.replace (atomico),
    para nunca deixar `path` truncado/parcialmente escrito se o processo
    morrer no meio da escrita (queda de energia, kill -9, disco cheio a
    meio caminho)."""
    tmp_path = f"{path}.tmp"
    try:
        with open(tmp_path, "w", newline="") as f:
            write_fn(f)
    except Exception:
        try:
            os.remove(tmp_path)
        except OSError:
            pass
        raise
    os.replace(tmp_path, path)
