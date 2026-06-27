"""Almacén de overrides en vivo (designaciones y árbitros descubiertos).

Es la *fuente de verdad* de los datos que llegan durante el torneo. El
actualizador lo reescribe; la API lo superpone sobre los datos base. También es
editable a mano si en algún momento se quiere forzar una designación.
"""

import json
import threading
from pathlib import Path

_LOCK = threading.Lock()
OVERRIDES_PATH = Path(__file__).resolve().parent.parent / "data" / "live_overrides.json"

_EMPTY = {"updated": None, "appointments": {}, "referees": {}}


def load() -> dict:
    try:
        data = json.loads(OVERRIDES_PATH.read_text(encoding="utf-8"))
        for k, v in _EMPTY.items():
            data.setdefault(k, v if not isinstance(v, dict) else {})
        return data
    except Exception:
        return {"updated": None, "appointments": {}, "referees": {}}


def save(data: dict) -> None:
    with _LOCK:
        OVERRIDES_PATH.write_text(
            json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
        )
