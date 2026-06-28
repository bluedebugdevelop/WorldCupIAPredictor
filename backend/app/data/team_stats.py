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

# Córners TOTALES por partido en los encuentros de cada selección (Mundial 2026,
# datos reales). Es la media de córners (ambos equipos) en sus partidos.
CORNERS_MATCH = {
    "TUR": 11.8, "CAN": 11.5, "BEL": 10.9, "ENG": 10.3, "GER": 10.1, "USA": 10.1,
    "CIV": 10.0, "BIH": 10.0, "ESP": 9.1, "NED": 8.9, "FRA": 8.7, "POR": 8.3,
    "BRA": 7.8, "MEX": 6.6, "ARG": 6.5, "AUT": 6.5,
}

# Amarillas RECIBIDAS por partido (Mundial 2026, datos reales). Este torneo se
# deja jugar mucho: se pitan menos faltas y se sacan pocas tarjetas.
YELLOWS_PG = {
    "PAR": 2.33, "HAI": 2.33, "CUW": 2.33, "BIH": 2.00, "SAU": 2.00,
    "IRN": 2.00, "EGY": 2.00, "URU": 1.67, "AUS": 1.67, "SCO": 1.67,
}

# Medias del torneo (para regularizar muestras de solo 3 partidos).
TOURNEY_GOALS_PG = 1.56       # goles por equipo y partido (3.12/partido)
TOURNEY_CORNERS_MATCH = 9.3   # córners totales por partido (media del torneo)
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


def corners_match(code: str, strength: float) -> float:
    """Córners TOTALES por partido típicos de esta selección en el torneo.

    Dato real si existe; si no, se estima (ligeramente más en equipos con pegada).
    Se regulariza hacia la media del torneo (3 partidos son poca muestra).
    """
    real = CORNERS_MATCH.get(code)
    base = real if real is not None else (8.6 + 1.6 * strength)
    return 0.72 * base + 0.28 * TOURNEY_CORNERS_MATCH
