"""Estadísticas REALES por equipo en el Mundial 2026.

El modelo da mucho peso a cómo ha rendido cada selección EN este torneo:
- goles a favor / en contra por partido (de las clasificaciones),
- córners por partido (datos reales del torneo; este Mundial tiene pocos córners
  por las nuevas reglas de saque, así que la cifra propia del equipo manda),
- posesión estimada a partir de la fuerza efectiva (quién tendrá más el balón).

``CORNERS_PG`` recoge córners por partido reales de las selecciones de las que
hay dato público; para el resto se estima desde su pegada. Reemplazable por un
feed de estadísticas (Opta/FBref) sin tocar el motor.
"""

from .tournament import STANDINGS

# Córners A FAVOR por partido (Mundial 2026, datos reales; pocos por las nuevas
# reglas). Fuente: estadísticas oficiales del torneo.
CORNERS_PG = {
    "CAN": 10.0, "ENG": 5.7, "BEL": 3.7, "TUR": 3.7, "NED": 3.3, "USA": 3.3,
    "URU": 3.3, "MAR": 3.3, "SWE": 3.0, "CZE": 3.0, "EGY": 3.0, "SUI": 3.0,
    "AUT": 3.0, "KOR": 3.0, "SEN": 3.0, "JPN": 3.0, "SCO": 2.7, "ESP": 2.7,
    "FRA": 2.3, "GER": 2.3, "BRA": 2.3,
}

# Amarillas RECIBIDAS por partido (Mundial 2026, datos reales). Este torneo se
# deja jugar mucho: se pitan menos faltas y se sacan pocas tarjetas.
YELLOWS_PG = {
    "PAR": 2.33, "HAI": 2.33, "CUW": 2.33, "BIH": 2.00, "SAU": 2.00,
    "IRN": 2.00, "EGY": 2.00, "URU": 1.67, "AUS": 1.67, "SCO": 1.67,
}

# Medias del torneo (para regularizar muestras de solo 3 partidos).
TOURNEY_GOALS_PG = 1.56       # goles por equipo y partido (3.12/partido)
TOURNEY_CORNERS_PG = 3.3      # córners a favor por equipo y partido
TOURNEY_YELLOWS_PG = 2.0      # amarillas por equipo y partido (pocas: se deja jugar)


def yellows_pg(code: str, strength: float) -> float:
    """Amarillas por partido que recibe la selección EN el torneo (regularizado).

    Dato real si existe; si no, se estima (los equipos más débiles, más a la
    defensiva, suelen ver más tarjetas). Se encoge hacia la media del torneo.
    """
    real = YELLOWS_PG.get(code)
    base = real if real is not None else (TOURNEY_YELLOWS_PG + 0.7 * (0.5 - strength))
    return 0.6 * base + 0.4 * TOURNEY_YELLOWS_PG


def goals_pg(code: str) -> tuple[float, float]:
    """(goles a favor, goles en contra) por partido de la selección EN el torneo.

    Usa cifras exactas si están; si solo hay diferencia de goles, las reparte
    en torno a la media del torneo.
    """
    s = STANDINGS.get(code)
    if not s or s.get("pld", 0) == 0:
        return TOURNEY_GOALS_PG, TOURNEY_GOALS_PG
    pld = s["pld"]
    if "gf" in s and "ga" in s:
        gf, ga = s["gf"], s["ga"]
    else:
        mean = TOURNEY_GOALS_PG * pld
        gf = max(0.6, mean + s["gd"] / 2.0)
        ga = max(0.6, mean - s["gd"] / 2.0)
    return gf / pld, ga / pld


def corners_pg(code: str, strength: float) -> float:
    """Córners a favor por partido: dato real del torneo si existe, regularizado.

    Sin dato, se estima desde la pegada del equipo. Se encoge hacia la media
    porque 3 partidos son poca muestra.
    """
    real = CORNERS_PG.get(code)
    base = real if real is not None else (1.6 + 3.2 * strength)
    # 65% rendimiento propio en el torneo, 35% media (estabiliza la muestra)
    return 0.65 * base + 0.35 * TOURNEY_CORNERS_PG
