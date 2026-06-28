"""Estado REAL del Mundial 2026: grupos, clasificaciones, calendario e intereses.

- ``STANDINGS``: clasificación real de la fase de grupos. Los grupos A-I ya la
  han completado (3 partidos); J, K y L disputan su última jornada hoy (27 jun),
  por lo que figuran con 2 partidos jugados.
- ``form_elo_delta``: ajuste de Elo por rendimiento dentro del torneo.
- ``FIXTURES``: calendario unificado (últimos partidos de grupos + Ronda de 32)
  con marca temporal UTC para ordenarlo cronológicamente; el front lo muestra en
  hora de España.
- ``team_stake`` / ``group_scenarios``: qué necesita cada equipo en la última
  jornada (clasificado, le vale el empate, necesita ganar, eliminado...) y el
  multiplicador de motivación que el predictor aplica.

Datos de fuentes en vivo del torneo. Preparado para refrescarse desde una API.
"""

from .teams import TEAMS_BY_CODE

# --- Clasificaciones reales (pld, w, d, l, gf, ga, gd, pts) ---
STANDINGS = {
    # Grupo A-I: fase de grupos COMPLETADA (3 jugados)
    "MEX": {"pld": 3, "w": 3, "d": 0, "l": 0, "gd": 6, "pts": 9},
    "RSA": {"pld": 3, "w": 1, "d": 1, "l": 1, "gd": -1, "pts": 4},
    "KOR": {"pld": 3, "w": 1, "d": 0, "l": 2, "gd": -1, "pts": 3},
    "CZE": {"pld": 3, "w": 0, "d": 1, "l": 2, "gd": -4, "pts": 1},

    "SUI": {"pld": 3, "w": 2, "d": 1, "l": 0, "gd": 4, "pts": 7},
    "CAN": {"pld": 3, "w": 1, "d": 1, "l": 1, "gd": 5, "pts": 4},
    "BIH": {"pld": 3, "w": 1, "d": 1, "l": 1, "gd": -1, "pts": 4},
    "QAT": {"pld": 3, "w": 0, "d": 1, "l": 2, "gd": -8, "pts": 1},

    "BRA": {"pld": 3, "w": 2, "d": 1, "l": 0, "gd": 6, "pts": 7},
    "MAR": {"pld": 3, "w": 2, "d": 1, "l": 0, "gd": 3, "pts": 7},
    "SCO": {"pld": 3, "w": 1, "d": 0, "l": 2, "gd": -3, "pts": 3},
    "HAI": {"pld": 3, "w": 0, "d": 0, "l": 3, "gd": -6, "pts": 0},

    "USA": {"pld": 3, "w": 2, "d": 0, "l": 1, "gd": 4, "pts": 6},
    "AUS": {"pld": 3, "w": 1, "d": 1, "l": 1, "gd": 0, "pts": 4},
    "PAR": {"pld": 3, "w": 1, "d": 1, "l": 1, "gd": -2, "pts": 4},
    "TUR": {"pld": 3, "w": 1, "d": 0, "l": 2, "gd": -2, "pts": 3},

    "GER": {"pld": 3, "w": 2, "d": 0, "l": 1, "gd": 6, "pts": 6},
    "CIV": {"pld": 3, "w": 2, "d": 0, "l": 1, "gd": 2, "pts": 6},
    "ECU": {"pld": 3, "w": 1, "d": 1, "l": 1, "gd": 0, "pts": 4},
    "CUW": {"pld": 3, "w": 0, "d": 1, "l": 2, "gd": -8, "pts": 1},

    "NED": {"pld": 3, "w": 2, "d": 1, "l": 0, "gd": 6, "pts": 7},
    "JPN": {"pld": 3, "w": 1, "d": 2, "l": 0, "gd": 4, "pts": 5},
    "SWE": {"pld": 3, "w": 1, "d": 1, "l": 1, "gd": 0, "pts": 4},
    "TUN": {"pld": 3, "w": 0, "d": 0, "l": 3, "gd": -10, "pts": 0},

    "BEL": {"pld": 3, "w": 1, "d": 2, "l": 0, "gd": 3, "pts": 5},
    "EGY": {"pld": 3, "w": 1, "d": 2, "l": 0, "gd": 2, "pts": 5},
    "IRN": {"pld": 3, "w": 1, "d": 0, "l": 2, "gd": 0, "pts": 3},
    "NZL": {"pld": 3, "w": 0, "d": 1, "l": 2, "gd": -5, "pts": 1},

    "ESP": {"pld": 3, "w": 2, "d": 1, "l": 0, "gd": 5, "pts": 7},
    "CPV": {"pld": 3, "w": 0, "d": 3, "l": 0, "gd": 0, "pts": 3},
    "URU": {"pld": 3, "w": 0, "d": 2, "l": 1, "gd": -1, "pts": 2},
    "SAU": {"pld": 3, "w": 0, "d": 1, "l": 2, "gd": -4, "pts": 1},

    "FRA": {"pld": 3, "w": 3, "d": 0, "l": 0, "gd": 8, "pts": 9},
    "NOR": {"pld": 3, "w": 2, "d": 0, "l": 1, "gd": 1, "pts": 6},
    "SEN": {"pld": 3, "w": 0, "d": 0, "l": 3, "gd": -3, "pts": 0},
    "IRQ": {"pld": 3, "w": 0, "d": 0, "l": 3, "gd": -6, "pts": 0},

    # Grupos J, K, L: FINALES (3 jugados) tras la última jornada.
    "ARG": {"pld": 3, "w": 3, "d": 0, "l": 0, "gf": 8, "ga": 1, "gd": 7, "pts": 9},
    "AUT": {"pld": 3, "w": 1, "d": 1, "l": 1, "gf": 6, "ga": 6, "gd": 0, "pts": 4},
    "ALG": {"pld": 3, "w": 1, "d": 1, "l": 1, "gf": 5, "ga": 7, "gd": -2, "pts": 4},
    "JOR": {"pld": 3, "w": 0, "d": 0, "l": 3, "gf": 3, "ga": 8, "gd": -5, "pts": 0},

    "COL": {"pld": 3, "w": 2, "d": 1, "l": 0, "gf": 4, "ga": 1, "gd": 3, "pts": 7},
    "POR": {"pld": 3, "w": 1, "d": 2, "l": 0, "gf": 6, "ga": 1, "gd": 5, "pts": 5},
    "COD": {"pld": 3, "w": 1, "d": 1, "l": 1, "gf": 4, "ga": 3, "gd": 1, "pts": 4},
    "UZB": {"pld": 3, "w": 0, "d": 0, "l": 3, "gf": 2, "ga": 11, "gd": -9, "pts": 0},

    "ENG": {"pld": 3, "w": 2, "d": 1, "l": 0, "gf": 6, "ga": 2, "gd": 4, "pts": 7},
    "CRO": {"pld": 3, "w": 2, "d": 0, "l": 1, "gf": 5, "ga": 5, "gd": 0, "pts": 6},
    "GHA": {"pld": 3, "w": 1, "d": 1, "l": 1, "gf": 2, "ga": 2, "gd": 0, "pts": 4},
    "PAN": {"pld": 3, "w": 0, "d": 0, "l": 3, "gf": 0, "ga": 4, "gd": -4, "pts": 0},
}

# La forma EN el Mundial pesa mucho: coeficientes altos y tope amplio para que
# el rendimiento real en el torneo domine sobre el nivel previo (Elo base).
FORM_CAP = 230.0


def form_elo_delta(code: str) -> float:
    """Ajuste de Elo según el rendimiento del equipo EN el torneo (peso alto)."""
    s = STANDINGS.get(code)
    if not s or s["pld"] == 0:
        return 0.0
    gdpg = s["gd"] / s["pld"]
    ppg = s["pts"] / s["pld"]
    delta = 40.0 * gdpg + 28.0 * (ppg - 1.5)
    return round(max(-FORM_CAP, min(FORM_CAP, delta)), 1)


# ====================================================================
# ESCENARIOS DE CLASIFICACIÓN (última jornada de grupos J, K, L)
# ====================================================================
# Emparejamientos restantes (local, visitante). La fase de grupos ya terminó,
# así que no quedan partidos: los intereses dejan de aplicarse.
REMAINING_PAIRINGS = {}

# Multiplicador de motivación que aplica el predictor según el interés.
# Incluye tanto el interés por CLASIFICAR como, para los ya clasificados, el
# interés por acabar 1º (mejor cruce en la Ronda de 32). Un equipo que ya tiene
# el 1º asegurado tiende a reservar; uno que se juega el 1º (o clasificar) empuja.
MOTIVATION = {
    "Eliminado": 0.90,
    "Necesita ganar": 1.07,
    "Necesita ganar y depende": 1.06,
    "Gana para ser 1º": 1.05,
    "Gana para pelear 1º": 1.04,
    "Pelea por clasificar": 1.04,
    "Depende de otros": 1.02,
    "Empate para ser 1º": 1.00,
    "Le vale el empate": 0.99,
    "Clasificado (2º)": 0.95,
    "Clasificado": 0.97,
    "1º asegurado": 0.93,
}


def _apply(table, match, outcome):
    """Aplica un resultado (1/X/2) a una tabla {code:[pts,gd,gf]} en marcha."""
    h, a = match
    if outcome == "1":
        table[h][0] += 3; table[h][1] += 1; table[h][2] += 1; table[a][1] -= 1
    elif outcome == "X":
        table[h][0] += 1; table[a][0] += 1; table[h][2] += 1; table[a][2] += 1
    else:  # "2"
        table[a][0] += 3; table[a][1] += 1; table[a][2] += 1; table[h][1] -= 1


# Puntos mínimos con los que un TERCERO entra entre los 8 mejores.
# En esta última jornada hay como mucho 7 terceros con 4 puntos (4 ya cerrados en
# los grupos A-I + a lo sumo 1 por cada grupo vivo J/K/L) y ningún tercero puede
# superar los 4 puntos, así que cualquier tercero con >=4 puntos entra; con <=3 se
# queda fuera (los 8 huecos se llenan con los terceros de 4 puntos y los de 3 con
# mejor diferencia ya cerrados).
THIRD_PLACE_CUTOFF = 4


def group_scenarios(group: str) -> dict:
    """Para cada equipo del grupo, su situación de cara a la última jornada.

    Considera tres niveles de interés:
      1. Clasificar (top-2 del grupo o repesca de los 8 mejores terceros).
      2. Para los ya clasificados, acabar 1º (mejor cruce en la Ronda de 32):
         "1º asegurado", "Empate para ser 1º", "Gana para ser 1º"...
    """
    pairing = REMAINING_PAIRINGS.get(group)
    if not pairing:
        return {}
    codes = [c for pair in pairing for c in pair]
    base = {c: [STANDINGS[c]["pts"], STANDINGS[c]["gd"], STANDINGS[c].get("gf", 0)] for c in codes}
    outcomes = ["1", "X", "2"]
    result = {}
    for c in codes:
        my = next(p for p in pairing if c in p)
        other = next(p for p in pairing if c not in p)
        is_home = my[0] == c
        quals, firsts = {}, {}  # resultado propio -> [por cada resultado del otro]
        for mo in outcomes:
            qrow, frow = [], []
            for oo in outcomes:
                tbl = {k: list(v) for k, v in base.items()}
                _apply(tbl, my, mo)
                _apply(tbl, other, oo)
                order = sorted(tbl, key=lambda x: (tbl[x][0], tbl[x][1], tbl[x][2]), reverse=True)
                pos = order.index(c)
                qrow.append(pos <= 1 or (pos == 2 and tbl[c][0] >= THIRD_PLACE_CUTOFF))
                frow.append(pos == 0)
            quals[mo] = qrow
            firsts[mo] = frow
        win_o = "1" if is_home else "2"
        loss_o = "2" if is_home else "1"
        qw, qd, ql = quals[win_o], quals["X"], quals[loss_o]
        fw, fd, fl = firsts[win_o], firsts["X"], firsts[loss_o]
        if not any(qw) and not any(qd) and not any(ql):
            st = "Eliminado"
        elif all(qw) and all(qd) and all(ql):
            # Clasificación asegurada: el interés pasa a ser la POSICIÓN (1º = mejor cruce).
            if all(fw) and all(fd) and all(fl):
                st = "1º asegurado"
            elif all(fd):
                st = "Empate para ser 1º"
            elif all(fw):
                st = "Gana para ser 1º"
            elif any(fw) or any(fd):
                st = "Gana para pelear 1º"
            else:
                st = "Clasificado (2º)"
        elif all(qd):
            st = "Le vale el empate"
        elif all(qw):
            st = "Necesita ganar"
        elif any(qw):
            st = "Necesita ganar y depende"
        else:
            st = "Depende de otros"
        result[c] = st
    return result


# Escenarios precalculados por equipo (código -> estado).
_TEAM_STAKE = {}
for _g in REMAINING_PAIRINGS:
    _TEAM_STAKE.update(group_scenarios(_g))


def team_stake(code: str):
    """Estado de clasificación del equipo, o None si su grupo ya terminó."""
    return _TEAM_STAKE.get(code)


def motivation_for(code: str) -> float:
    st = team_stake(code)
    return MOTIVATION.get(st, 1.0) if st else 1.0


# ====================================================================
# CALENDARIO UNIFICADO (hora en UTC para ordenar; el front muestra hora ES)
# ====================================================================
FIXTURES = [
    # --- Última jornada de la fase de grupos (HOY, 27 jun) ---
    {"phase": "Grupo L · J3", "a": "PAN", "b": "ENG", "venue": "MetLife Stadium, East Rutherford",   "utc": "2026-06-27T21:00:00Z", "ref": "aljassim"},
    {"phase": "Grupo L · J3", "a": "CRO", "b": "GHA", "venue": "Lincoln Financial Field, Filadelfia", "utc": "2026-06-27T21:00:00Z"},
    {"phase": "Grupo K · J3", "a": "COL", "b": "POR", "venue": "Hard Rock Stadium, Miami",            "utc": "2026-06-27T23:30:00Z", "ref": "faghani"},
    {"phase": "Grupo K · J3", "a": "COD", "b": "UZB", "venue": "Mercedes-Benz Stadium, Atlanta",      "utc": "2026-06-27T23:30:00Z"},
    {"phase": "Grupo J · J3", "a": "JOR", "b": "ARG", "venue": "AT&T Stadium, Arlington",             "utc": "2026-06-28T02:00:00Z", "ref": "kovacs"},
    {"phase": "Grupo J · J3", "a": "ALG", "b": "AUT", "venue": "Arrowhead Stadium, Kansas City",      "utc": "2026-06-28T02:00:00Z"},

    # --- Ronda de 32 ---
    {"phase": "Ronda de 32 · P73", "a": "RSA", "b": "CAN",                 "venue": "SoFi Stadium, Inglewood",            "utc": "2026-06-28T19:00:00Z"},
    {"phase": "Ronda de 32 · P76", "a": "BRA", "b": "JPN",                 "venue": "NRG Stadium, Houston",               "utc": "2026-06-29T17:00:00Z"},
    {"phase": "Ronda de 32 · P74", "a": "GER", "b": "PAR",                 "venue": "Gillette Stadium, Foxborough",       "utc": "2026-06-29T20:30:00Z"},
    {"phase": "Ronda de 32 · P75", "a": "NED", "b": "MAR",                 "venue": "Estadio BBVA, Guadalupe",            "utc": "2026-06-30T01:00:00Z"},
    {"phase": "Ronda de 32 · P78", "a": "CIV", "b": "NOR",                 "venue": "AT&T Stadium, Arlington",            "utc": "2026-06-30T17:00:00Z"},
    {"phase": "Ronda de 32 · P77", "a": "FRA", "b": "SWE",                 "venue": "MetLife Stadium, East Rutherford",   "utc": "2026-06-30T21:00:00Z"},
    {"phase": "Ronda de 32 · P79", "a": "MEX", "b": "ECU",                 "venue": "Estadio Azteca, Ciudad de México",   "utc": "2026-07-01T01:00:00Z"},
    {"phase": "Ronda de 32 · P80", "a": "ENG", "b": "COD",                 "venue": "Mercedes-Benz Stadium, Atlanta",     "utc": "2026-07-01T16:00:00Z"},
    {"phase": "Ronda de 32 · P82", "a": "BEL", "b": "SEN",                 "venue": "Lumen Field, Seattle",               "utc": "2026-07-01T20:00:00Z"},
    {"phase": "Ronda de 32 · P81", "a": "USA", "b": "BIH",                 "venue": "Levi's Stadium, Santa Clara",        "utc": "2026-07-02T00:00:00Z"},
    {"phase": "Ronda de 32 · P84", "a": "ESP", "b": "AUT",                 "venue": "SoFi Stadium, Inglewood",            "utc": "2026-07-02T19:00:00Z"},
    {"phase": "Ronda de 32 · P83", "a": "POR", "b": "CRO",                 "venue": "BMO Field, Toronto",                 "utc": "2026-07-02T23:00:00Z"},
    {"phase": "Ronda de 32 · P85", "a": "SUI", "b": "ALG",                 "venue": "BC Place, Vancouver",                "utc": "2026-07-03T03:00:00Z"},
    {"phase": "Ronda de 32 · P88", "a": "AUS", "b": "EGY",                 "venue": "AT&T Stadium, Arlington",            "utc": "2026-07-03T18:00:00Z"},
    {"phase": "Ronda de 32 · P86", "a": "ARG", "b": "CPV",                 "venue": "Hard Rock Stadium, Miami",           "utc": "2026-07-03T22:00:00Z"},
    {"phase": "Ronda de 32 · P87", "a": "COL", "b": "GHA",                 "venue": "Arrowhead Stadium, Kansas City",     "utc": "2026-07-04T01:30:00Z"},
]

KNOCKOUT_DATES = [
    {"round": "Fin fase de grupos", "dates": "27 jun"},
    {"round": "Ronda de 32", "dates": "28 jun – 3 jul"},
    {"round": "Octavos (R16)", "dates": "4 – 7 jul"},
    {"round": "Cuartos", "dates": "9 – 11 jul"},
    {"round": "Semifinales", "dates": "14 – 15 jul"},
    {"round": "Final", "dates": "19 jul · MetLife Stadium"},
]


# ====================================================================
# BRACKET — árbol completo R32 -> Final (estructura oficial 2026).
# 'a'/'b' son código de equipo (R32) o referencia "W{n}"/"L{n}" = ganador/
# perdedor del partido n. ``build_bracket`` resuelve los equipos y avanza a los
# ganadores según los resultados (de los overrides en vivo / feed del torneo).
# ====================================================================
BRACKET = [
    # Ronda de 32
    {"m": 73, "round": "R32", "a": "RSA", "b": "CAN"},
    {"m": 74, "round": "R32", "a": "GER", "b": "PAR"},
    {"m": 75, "round": "R32", "a": "NED", "b": "MAR"},
    {"m": 76, "round": "R32", "a": "BRA", "b": "JPN"},
    {"m": 77, "round": "R32", "a": "FRA", "b": "SWE"},
    {"m": 78, "round": "R32", "a": "CIV", "b": "NOR"},
    {"m": 79, "round": "R32", "a": "MEX", "b": "ECU"},
    {"m": 80, "round": "R32", "a": "ENG", "b": "COD"},
    {"m": 81, "round": "R32", "a": "USA", "b": "BIH"},
    {"m": 82, "round": "R32", "a": "BEL", "b": "SEN"},
    {"m": 83, "round": "R32", "a": "POR", "b": "CRO"},
    {"m": 84, "round": "R32", "a": "ESP", "b": "AUT"},
    {"m": 85, "round": "R32", "a": "SUI", "b": "ALG"},
    {"m": 86, "round": "R32", "a": "ARG", "b": "CPV"},
    {"m": 87, "round": "R32", "a": "COL", "b": "GHA"},
    {"m": 88, "round": "R32", "a": "AUS", "b": "EGY"},
    # Octavos (R16)
    {"m": 89, "round": "R16", "a": "W74", "b": "W77"},
    {"m": 90, "round": "R16", "a": "W73", "b": "W75"},
    {"m": 91, "round": "R16", "a": "W76", "b": "W78"},
    {"m": 92, "round": "R16", "a": "W79", "b": "W80"},
    {"m": 93, "round": "R16", "a": "W83", "b": "W84"},
    {"m": 94, "round": "R16", "a": "W81", "b": "W82"},
    {"m": 95, "round": "R16", "a": "W86", "b": "W88"},
    {"m": 96, "round": "R16", "a": "W85", "b": "W87"},
    # Cuartos
    {"m": 97, "round": "QF", "a": "W89", "b": "W90"},
    {"m": 98, "round": "QF", "a": "W93", "b": "W94"},
    {"m": 99, "round": "QF", "a": "W91", "b": "W92"},
    {"m": 100, "round": "QF", "a": "W95", "b": "W96"},
    # Semifinales
    {"m": 101, "round": "SF", "a": "W97", "b": "W98"},
    {"m": 102, "round": "SF", "a": "W99", "b": "W100"},
    # Final y 3er puesto
    {"m": 104, "round": "F", "a": "W101", "b": "W102"},
    {"m": 103, "round": "3P", "a": "L101", "b": "L102"},
]

ROUND_LABELS = {"R32": "Ronda de 32", "R16": "Octavos", "QF": "Cuartos",
                "SF": "Semifinales", "F": "Final", "3P": "3.er puesto"}

_BRACKET_BY_M = {b["m"]: b for b in BRACKET}


def _team_brief(code):
    t = TEAMS_BY_CODE.get(code)
    return {"code": code, "name": t["name"], "iso": t.get("iso", "")} if t else None


def build_bracket(results: dict) -> list:
    """Resuelve el bracket con los resultados disponibles.

    ``results``: dict "CODEA-CODEB" -> {"a": golesA, "b": golesB, "w": código
    ganador} (en cualquier orden de claves). Devuelve cada partido con sus dos
    equipos resueltos (o None si aún no se conocen) y el ganador si ya se jugó.
    """
    cache = {}

    def result_for(ca, cb):
        if not ca or not cb:
            return None
        return results.get(f"{ca}-{cb}") or results.get(f"{cb}-{ca}")

    def resolve(m):
        if m in cache:
            return cache[m]
        spec = _BRACKET_BY_M[m]
        cache[m] = {"a": None, "b": None, "w": None, "l": None}  # evita recursión infinita

        def side(ref):
            if ref in TEAMS_BY_CODE:
                return ref
            kind, n = ref[0], int(ref[1:])
            r = resolve(n)
            return r["w"] if kind == "W" else r["l"]

        ca, cb = side(spec["a"]), side(spec["b"])
        res = result_for(ca, cb)
        w = lcode = None
        if res and ca and cb:
            wcode = res.get("w")
            if not wcode and res.get("a") is not None and res.get("b") is not None:
                if res["a"] != res["b"]:
                    wcode = ca if res["a"] > res["b"] else cb
            if wcode in (ca, cb):
                w = wcode
                lcode = cb if wcode == ca else ca
        cache[m] = {"a": ca, "b": cb, "w": w, "l": lcode, "res": res}
        return cache[m]

    out = []
    for spec in BRACKET:
        r = resolve(spec["m"])
        score = None
        if r.get("res") and r["res"].get("a") is not None:
            score = f"{r['res']['a']}-{r['res']['b']}"
        out.append({
            "m": spec["m"],
            "round": spec["round"],
            "round_label": ROUND_LABELS[spec["round"]],
            "a": _team_brief(r["a"]),
            "b": _team_brief(r["b"]),
            "winner": r["w"],
            "score": score,
        })
    return out
