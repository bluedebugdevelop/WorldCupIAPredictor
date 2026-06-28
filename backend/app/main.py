"""WorldCupIAPredictor — API y servidor de la interfaz web.

Punto de entrada FastAPI. Expone los endpoints de catálogo (selecciones,
árbitros) y el endpoint de predicción que ejecuta la simulación Monte Carlo.
Sirve además el frontend estático desde ``/``.
"""

import asyncio
import os
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .data.teams import TEAMS, TEAMS_BY_CODE
from .data.referees import REFEREES, REFEREES_BY_ID
from .data.tournament import (
    STANDINGS, FIXTURES, KNOCKOUT_DATES, form_elo_delta,
    team_stake, motivation_for, build_bracket,
)
from .engine.simulate import simulate
from .schemas import PredictRequest
from .live import store as live_store
from .live import updater as live_updater

# Intervalo de auto-refresco de designaciones (segundos).
REFRESH_INTERVAL = 3 * 3600


def all_referees() -> list[dict]:
    """Roster base + árbitros descubiertos en vivo."""
    extra = list(live_store.load().get("referees", {}).values())
    return REFEREES + extra


def ref_by_id(rid: str):
    return REFEREES_BY_ID.get(rid) or live_store.load().get("referees", {}).get(rid)


def appointed_ref(a: str, b: str):
    """Árbitro designado (override en vivo) para un emparejamiento, en cualquier orden."""
    ap = live_store.load().get("appointments", {})
    return ap.get(f"{a}-{b}") or ap.get(f"{b}-{a}")

app = FastAPI(
    title="WorldCupIAPredictor",
    description="Motor de predicción del Mundial 2026 (Poisson + Monte Carlo + factor árbitro)",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ruta del frontend: por defecto relativa al backend; configurable (Vercel).
FRONTEND_DIR = Path(os.environ.get(
    "FRONTEND_DIR", Path(__file__).resolve().parent.parent.parent / "frontend"))

# En Vercel (serverless) no hay proceso persistente: el refresco va por cron.
IS_SERVERLESS = bool(os.environ.get("VERCEL"))


@app.get("/api/teams")
def get_teams():
    """Catálogo de selecciones, ordenado por Elo descendente."""
    return sorted(TEAMS, key=lambda t: -t["elo"])


@app.get("/api/referees")
def get_referees():
    """Catálogo de árbitros (roster real + descubiertos en vivo)."""
    return all_referees()


@app.get("/api/status")
def get_status():
    """Estado de la última sincronización de datos en vivo."""
    data = live_store.load()
    return {
        "updated": data.get("updated"),
        "appointments": len(data.get("appointments", {})),
        "referees_live": len(data.get("referees", {})),
    }


@app.api_route("/api/refresh", methods=["GET", "POST"])
async def refresh_now():
    """Fuerza una actualización de designaciones (lo llama también el cron de Vercel)."""
    return await asyncio.to_thread(live_updater.refresh)


@app.on_event("startup")
async def _start_auto_refresh():
    """Refresca al arrancar y cada REFRESH_INTERVAL (solo con proceso persistente)."""
    if IS_SERVERLESS:
        return  # en Vercel el refresco lo dispara el cron -> /api/refresh
    async def loop():
        while True:
            try:
                await asyncio.to_thread(live_updater.refresh)
            except Exception:
                pass
            await asyncio.sleep(REFRESH_INTERVAL)
    asyncio.create_task(loop())


@app.get("/api/groups")
def get_groups():
    """Los 12 grupos con su clasificación real, ordenada por posición."""
    groups: dict[str, list] = {}
    for t in TEAMS:
        row = dict(STANDINGS.get(t["code"], {}))
        row.update({"code": t["code"], "name": t["name"], "flag": t["flag"],
                    "iso": t.get("iso", ""), "elo": t["elo"]})
        row["form"] = form_elo_delta(t["code"])
        groups.setdefault(t["group"], []).append(row)
    for g in groups.values():
        g.sort(key=lambda r: (-r.get("pts", 0), -r.get("gd", 0)))
    return {g: groups[g] for g in sorted(groups)}


@app.get("/api/bracket")
def get_bracket():
    """Bracket eliminatorio resuelto con los resultados disponibles."""
    results = live_store.load().get("results", {})
    matches = build_bracket(results)
    rounds_order = ["R32", "R16", "QF", "SF", "F", "3P"]
    by_round = {r: [] for r in rounds_order}
    for m in matches:
        by_round[m["round"]].append(m)
    return {"rounds": [{"key": r, "label": by_round[r][0]["round_label"] if by_round[r] else r,
                        "matches": by_round[r]} for r in rounds_order]}


# Fases del torneo, en orden, y anclas de fecha para las rondas del bracket que
# aún no tienen horario/sede asignados.
PHASES = [
    {"key": "grupos", "label": "Fase de grupos"},
    {"key": "r32", "label": "Ronda de 32"},
    {"key": "r16", "label": "Octavos"},
    {"key": "qf", "label": "Cuartos"},
    {"key": "sf", "label": "Semifinales"},
    {"key": "final", "label": "Final"},
]
_BRACKET_PHASE = {"R16": "r16", "QF": "qf", "SF": "sf", "F": "final", "3P": "final"}
_ROUND_UTC = {"R16": "2026-07-04T16:00:00Z", "QF": "2026-07-09T16:00:00Z",
              "SF": "2026-07-14T18:00:00Z", "3P": "2026-07-18T18:00:00Z",
              "F": "2026-07-19T19:00:00Z"}


def _fixture_phase(phase_str: str) -> str:
    if phase_str.startswith("Grupo"):
        return "grupos"
    return "r32"


@app.get("/api/schedule")
def get_schedule():
    """Calendario por fases: cada partido con su fase, orden cronológico.

    Incluye grupos + Ronda de 32 (con horario/sede) y las rondas siguientes del
    bracket (equipos según resultados). Indica la fase ACTUAL del torneo.
    """
    def expand(side: str):
        t = TEAMS_BY_CODE.get(side)
        if not t:
            return {"label": side}
        return {"code": t["code"], "name": t["name"], "flag": t["flag"],
                "iso": t.get("iso", ""), "stake": team_stake(t["code"])}

    def ref_info(rid):
        r = ref_by_id(rid)
        return {"id": r["id"], "name": r["name"], "country": r["country"],
                "style": r["style"], "estimated": r.get("estimated", False)} if r else None

    def brief(b):  # equipo del bracket (ya {code,name,iso}) o "Por definir"
        return {**b, "stake": None} if b else {"label": "Por definir"}

    # Grupos + Ronda de 32 (datos completos)
    fixtures = [
        {**f, "phase_key": _fixture_phase(f["phase"]),
         "a": expand(f["a"]), "b": expand(f["b"]),
         "referee": ref_info(appointed_ref(f["a"], f["b"]) or f.get("ref")),
         "playable": f["a"] in TEAMS_BY_CODE and f["b"] in TEAMS_BY_CODE}
        for f in FIXTURES
    ]

    # Rondas siguientes (Octavos -> Final) desde el bracket
    results = live_store.load().get("results", {})
    for m in build_bracket(results):
        if m["round"] not in _BRACKET_PHASE:
            continue
        fixtures.append({
            "phase": m["round_label"] + (" · 3.er puesto" if m["round"] == "3P" else ""),
            "phase_key": _BRACKET_PHASE[m["round"]],
            "utc": _ROUND_UTC[m["round"]], "venue": None, "referee": None,
            "a": brief(m["a"]), "b": brief(m["b"]),
            "playable": bool(m["a"] and m["b"]),
            "score": m.get("score"), "winner": m.get("winner"),
        })

    fixtures.sort(key=lambda f: f["utc"])

    # Fase actual: la primera (en orden) con algún partido aún no jugado.
    now = datetime.now(timezone.utc).isoformat()
    current = PHASES[-1]["key"]
    for ph in PHASES:
        if any(f["phase_key"] == ph["key"] and f["utc"] > now for f in fixtures):
            current = ph["key"]
            break

    return {"fixtures": fixtures, "phases": PHASES, "current_phase": current,
            "rounds": KNOCKOUT_DATES}


def _with_form(team: dict, use_form: bool) -> dict:
    """Copia del equipo con el Elo ajustado por forma y su interés en la jornada."""
    t = dict(team)
    t["elo_base"] = team["elo"]
    delta = form_elo_delta(team["code"]) if use_form else 0.0
    t["form_delta"] = delta
    t["elo"] = team["elo"] + delta
    t["stake"] = team_stake(team["code"])
    return t


@app.post("/api/predict")
def predict(req: PredictRequest):
    """Ejecuta la simulación para un emparejamiento y devuelve las predicciones."""
    team_a = TEAMS_BY_CODE.get(req.team_a)
    team_b = TEAMS_BY_CODE.get(req.team_b)
    referee = ref_by_id(req.referee)

    if team_a is None or team_b is None:
        raise HTTPException(404, "Selección no encontrada")
    if referee is None:
        raise HTTPException(404, "Árbitro no encontrado")
    if req.team_a == req.team_b:
        raise HTTPException(400, "Las dos selecciones deben ser distintas")

    ta = _with_form(team_a, req.use_form)
    tb = _with_form(team_b, req.use_form)
    # Intereses de la jornada: solo se aplican fuera de eliminatoria.
    mot_a = motivation_for(team_a["code"]) if not req.knockout else 1.0
    mot_b = motivation_for(team_b["code"]) if not req.knockout else 1.0
    return simulate(
        ta, tb, referee,
        neutral=req.neutral, knockout=req.knockout,
        mot_a=mot_a, mot_b=mot_b, n_sims=req.n_sims,
    )


# --- Frontend estático (se monta al final para no eclipsar /api) ---
if FRONTEND_DIR.exists():
    @app.get("/")
    def index():
        return FileResponse(FRONTEND_DIR / "index.html")

    app.mount("/", StaticFiles(directory=str(FRONTEND_DIR)), name="frontend")
