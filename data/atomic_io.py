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
        os.replace(tmp_path, path)
    except Exception:
        # Cobre tanto falha ao escrever o .tmp quanto falha do proprio
        # os.replace (ex: neste repo, que vive numa pasta sincronizada pelo
        # OneDrive, o cliente de sync pode segurar o arquivo brevemente e
        # fazer o replace falhar mesmo com o .tmp escrito com sucesso).
        try:
            os.remove(tmp_path)
        except OSError:
            pass
        raise
