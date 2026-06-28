"""Almacén de overrides en vivo (designaciones y árbitros descubiertos).

Es la *fuente de verdad* de los datos que llegan durante el torneo. El
actualizador lo reescribe; la API lo superpone sobre los datos base.

Dos backends, elegidos automáticamente:
  - **Supabase** (Postgres) si están definidas las variables ``SUPABASE_URL`` y
    ``SUPABASE_SERVICE_KEY``. Es el modo para producción (Vercel), donde el disco
    es de solo lectura / efímero. Guarda el blob en la tabla ``kv_store`` bajo la
    clave ``live`` (ver ``supabase/schema.sql``).
  - **Fichero local** (``data/live_overrides.json``) en desarrollo. También
    editable a mano.
"""

import json
import os
import threading
import urllib.request
from pathlib import Path

_LOCK = threading.Lock()
OVERRIDES_PATH = Path(__file__).resolve().parent.parent / "data" / "live_overrides.json"

_EMPTY = {"updated": None, "appointments": {}, "referees": {}, "results": {}}

SUPABASE_URL = os.environ.get("SUPABASE_URL", "").rstrip("/")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY") or os.environ.get("SUPABASE_KEY")
USE_SUPABASE = bool(SUPABASE_URL and SUPABASE_KEY)

_KV_TABLE = "kv_store"
_KV_KEY = "live"
_TIMEOUT = 15


def _normalize(data: dict) -> dict:
    for k, v in _EMPTY.items():
        data.setdefault(k, v if not isinstance(v, dict) else {})
    return data


# ---------------- Supabase (PostgREST) ----------------
def _sb_headers() -> dict:
    return {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
    }


def _sb_load() -> dict:
    url = f"{SUPABASE_URL}/rest/v1/{_KV_TABLE}?key=eq.{_KV_KEY}&select=value"
    req = urllib.request.Request(url, headers=_sb_headers())
    with urllib.request.urlopen(req, timeout=_TIMEOUT) as resp:
        rows = json.load(resp)
    if rows and isinstance(rows[0].get("value"), dict):
        return _normalize(dict(rows[0]["value"]))
    return dict(_EMPTY)


def _sb_save(data: dict) -> None:
    url = f"{SUPABASE_URL}/rest/v1/{_KV_TABLE}?on_conflict=key"
    body = json.dumps([{"key": _KV_KEY, "value": data}]).encode("utf-8")
    headers = _sb_headers()
    headers["Prefer"] = "resolution=merge-duplicates"
    req = urllib.request.Request(url, data=body, headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=_TIMEOUT):
        pass


# ---------------- Fichero local ----------------
def _file_load() -> dict:
    try:
        return _normalize(json.loads(OVERRIDES_PATH.read_text(encoding="utf-8")))
    except Exception:
        return dict(_EMPTY)


def _file_save(data: dict) -> None:
    with _LOCK:
        OVERRIDES_PATH.write_text(
            json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
        )


# ---------------- API pública ----------------
def load() -> dict:
    if USE_SUPABASE:
        try:
            return _sb_load()
        except Exception:
            return dict(_EMPTY)
    return _file_load()


def save(data: dict) -> None:
    if USE_SUPABASE:
        _sb_save(data)
    else:
        _file_save(data)
