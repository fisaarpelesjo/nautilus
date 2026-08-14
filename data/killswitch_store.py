import json
import os
from datetime import datetime

from data.atomic_io import atomic_write
from data.paths import KILLSWITCH_FILE


def load_killswitch() -> bool:
    if not os.path.exists(KILLSWITCH_FILE):
        return False
    with open(KILLSWITCH_FILE) as f:
        try:
            return bool(json.load(f).get("active", False))
        except json.JSONDecodeError:
            return False


def save_killswitch(active: bool):
    payload = {"active": active, "toggled_at": datetime.now().isoformat()}
    atomic_write(KILLSWITCH_FILE, lambda f: json.dump(payload, f, indent=2))
