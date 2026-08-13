import json
import os

from data.atomic_io import atomic_write
from data.paths import STATE_FILE


def save_state(state: dict):
    atomic_write(STATE_FILE, lambda f: json.dump(state, f, indent=2, default=str))


def load_state() -> dict:
    if not os.path.exists(STATE_FILE):
        return {}
    with open(STATE_FILE) as f:
        try:
            return json.load(f)
        except json.JSONDecodeError as e:
            # Nao trata como "sem estado" (retornar {}) -- isso esconderia
            # posicoes abertas de verdade e o bot poderia comprar de novo
            # achando que nao tem nada aberto. Falha alto e claro em vez de
            # perder o estado silenciosamente (constitution P1).
            raise RuntimeError(
                f"{STATE_FILE} esta corrompido ({e}). Nao inicializando com "
                "estado vazio automaticamente -- restaure de um backup ou "
                "apague o arquivo manualmente so se tiver certeza de que nao "
                "ha posicao aberta de verdade na exchange."
            ) from e
