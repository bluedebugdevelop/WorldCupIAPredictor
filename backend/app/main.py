"""WorldCupIAPredictor — API y servidor de la interfaz web.

Punto de entrada FastAPI. Expone los endpoints de catálogo (selecciones,
árbitros) y el endpoint de predicción que ejecuta la simulación Monte Carlo.
Sirve además el frontend estático desde ``/``.
"""

import asyncio
import os
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .data.teams import TEAMS, TEAMS_BY_CODE
from .data.referees import REFEREES, REFEREES_BY_ID
from .data.tournament import (
    STANDINGS, FIXTURES, KNOCKOUT_DATES, form_elo_delta,
    team_stake, motivation_for,
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


@app.get("/api/schedule")
def get_schedule():
    """Calendario unificado (grupos restantes + Ronda de 32), orden cronológico."""
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

    fixtures = [
        {**f, "a": expand(f["a"]), "b": expand(f["b"]),
         "referee": ref_info(appointed_ref(f["a"], f["b"]) or f.get("ref")),
         "playable": f["a"] in TEAMS_BY_CODE and f["b"] in TEAMS_BY_CODE}
        for f in FIXTURES
    ]
    fixtures.sort(key=lambda f: f["utc"])
    return {"fixtures": fixtures, "rounds": KNOCKOUT_DATES}


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
