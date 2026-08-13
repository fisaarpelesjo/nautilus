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
        return json.load(f)
