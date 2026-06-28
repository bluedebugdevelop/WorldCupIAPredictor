"""Modelo estadístico del partido.

Convierte la fuerza (Elo normalizado) de cada selección en los parámetros
lambda (medias) de las distribuciones de Poisson que gobiernan goles, córners
y tarjetas. Es la parte "determinista" del motor: dado un emparejamiento y un
árbitro, calcula las medias esperadas. La parte estocástica (muestreo y
agregación de miles de partidos) vive en ``simulate.py``.

Fundamento: un modelo bivariante de Poisson para los goles es el estándar de
facto en la predicción de fútbol (Maher 1982; Dixon-Coles 1997) y es el que
utilizan modelos públicos como el SPI de FiveThirtyEight.
"""

import math
from dataclasses import dataclass

from ..data.teams import team_strength
from ..data.team_stats import goals_pg, corners_pg, TOURNEY_GOALS_PG

# --- Constantes CALIBRADAS al Mundial 2026 (datos reales del torneo) ---
# El torneo va muy goleador: ~3.12 goles/partido (vs 2.56 en 2022) y se pitan
# menos faltas, con menos tarjetas. Los córners se ajustan a las nuevas reglas.
BASE_GOALS = 1.56          # goles medios por equipo (3.12/partido en este Mundial)
GOAL_SPREAD = 1.25         # sensibilidad de los goles a la diferencia de fuerza
HOME_ADVANTAGE = 1.18      # multiplicador de ventaja de campo (sede no neutral)

BASE_CORNERS = 9.6         # córners totales/partido (nuevas reglas de saque)
CORNER_DOMINANCE = 0.9     # cómo se reparten los córners según el ataque

# Peso del rendimiento REAL del torneo (goles a favor/en contra) frente al nivel
# previo (Elo). Alto: lo que hace el equipo en este Mundial manda.
TOURNAMENT_GOAL_WEIGHT = 0.62

# Menos faltas -> menos tarjetas que la media histórica de los árbitros.
TOURNAMENT_CARD_FACTOR = 0.78
BASE_YELLOWS_TENSION = 1.0
TENSION_MAX_BONUS = 0.30   # los partidos igualados generan más tarjetas
KNOCKOUT_BONUS = 0.20      # eliminatoria: más tensión y más tarjetas
KNOCKOUT_GOAL_FACTOR = 0.90  # eliminatoria: más miedo a perder, partidos atascados


@dataclass
class MatchLambdas:
    """Medias (lambda) de Poisson resultantes para un emparejamiento."""
    goals_a: float
    goals_b: float
    corners_a: float
    corners_b: float
    yellows_a: float
    yellows_b: float
    reds_total: float
    penalties_total: float
    tension: float
    possession_a: float


def _att_def(strength: float) -> tuple[float, float]:
    """Factores multiplicativos de ataque y defensa centrados en 1.0.

    Equipos fuertes: ataque > 1 (marcan más), defensa < 1 (encajan menos).
    """
    att = math.exp(GOAL_SPREAD * (strength - 0.5))
    dfn = math.exp(-GOAL_SPREAD * (strength - 0.5))
    return att, dfn


def compute_lambdas(team_a: dict, team_b: dict, referee: dict,
                    neutral: bool = True, knockout: bool = False,
                    mot_a: float = 1.0, mot_b: float = 1.0) -> MatchLambdas:
    """Calcula las medias de Poisson para A (local nominal) vs B.

    ``mot_a``/``mot_b`` son multiplicadores de motivación (intereses del equipo
    en la jornada): un equipo que necesita ganar empuja más (sube su ataque y la
    tensión); uno ya clasificado o eliminado rinde algo por debajo.
    """
    sa, sb = team_strength(team_a), team_strength(team_b)
    att_a, def_a = _att_def(sa)
    att_b, def_b = _att_def(sb)
    ca, cb = team_a["code"], team_b["code"]

    home = 1.0 if neutral else HOME_ADVANTAGE

    # --- Posesión estimada (quién tendrá más el balón), por diferencia de Elo
    #     efectivo (que ya incluye la forma del torneo) y la ventaja de campo.
    elo_diff = team_a["elo"] - team_b["elo"] + (45.0 if not neutral else 0.0)
    poss_a = 1.0 / (1.0 + 10.0 ** (-elo_diff / 320.0))
    poss_a = max(0.30, min(0.70, poss_a))
    poss_b = 1.0 - poss_a

    # --- Goles: el rendimiento REAL del torneo (goles a favor/en contra por
    #     partido) pesa mucho; se mezcla con el modelo de Elo para estabilizar.
    gf_a, ga_a = goals_pg(ca)
    gf_b, ga_b = goals_pg(cb)
    tour_a = gf_a * ga_b / TOURNEY_GOALS_PG     # ataque de A vs defensa de B
    tour_b = gf_b * ga_a / TOURNEY_GOALS_PG
    elo_a = BASE_GOALS * att_a * def_b
    elo_b = BASE_GOALS * att_b * def_a
    w = TOURNAMENT_GOAL_WEIGHT
    ko = KNOCKOUT_GOAL_FACTOR if knockout else 1.0
    lam_goals_a = (w * tour_a + (1 - w) * elo_a) * home * mot_a * ko
    lam_goals_b = (w * tour_b + (1 - w) * elo_b) * mot_b * ko

    # --- Tensión del partido: mayor cuanto más igualado (y en eliminatorias) ---
    evenness = 1.0 - abs(sa - sb)            # 1 = idénticos, 0 = paliza
    tension = BASE_YELLOWS_TENSION + TENSION_MAX_BONUS * evenness
    if knockout:
        tension += KNOCKOUT_BONUS
    # un equipo necesitado de ganar mete más intensidad/tarjetas
    tension += 0.5 * max(mot_a - 1.0, mot_b - 1.0, 0.0)

    # --- Córners: dominan los córners REALES del equipo en el torneo, ajustados
    #     por quién tiene más la pelota (más posesión -> más córners).
    lam_corners_a = corners_pg(ca, sa) * (0.55 + 0.90 * poss_a)
    lam_corners_b = corners_pg(cb, sb) * (0.55 + 0.90 * poss_b)

    # --- Tarjetas: parten de la media del árbitro, escaladas al entorno de
    #     pocas faltas del Mundial 2026, y moduladas por la tensión del partido.
    total_yellows = referee["yellows"] * tension * TOURNAMENT_CARD_FACTOR
    # el equipo más débil (más a la defensiva) tiende a recibir algo más
    disc_share_a = 0.5 - 0.12 * (sa - sb)
    lam_yellows_a = total_yellows * disc_share_a
    lam_yellows_b = total_yellows * (1.0 - disc_share_a)

    lam_reds = referee["reds"] * tension * TOURNAMENT_CARD_FACTOR
    lam_penalties = referee["penalties"]

    return MatchLambdas(
        goals_a=lam_goals_a, goals_b=lam_goals_b,
        corners_a=lam_corners_a, corners_b=lam_corners_b,
        yellows_a=lam_yellows_a, yellows_b=lam_yellows_b,
        reds_total=lam_reds, penalties_total=lam_penalties,
        tension=tension, possession_a=poss_a,
    )
