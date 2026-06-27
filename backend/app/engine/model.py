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
from ..data.referees import AVG_YELLOWS, AVG_REDS, AVG_PENALTIES

# --- Constantes calibradas para fútbol internacional ---
BASE_GOALS = 1.35          # goles medios por equipo y partido
GOAL_SPREAD = 1.25         # sensibilidad de los goles a la diferencia de fuerza
HOME_ADVANTAGE = 1.18      # multiplicador de ventaja de campo (sede no neutral)

BASE_CORNERS = 10.6        # córners totales medios por partido
CORNER_DOMINANCE = 0.9     # cómo se reparten los córners según el ataque

BASE_YELLOWS_TENSION = 1.0
TENSION_MAX_BONUS = 0.30   # los partidos igualados generan más tarjetas
KNOCKOUT_BONUS = 0.12      # plus de tensión en eliminatorias


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

    home = 1.0 if neutral else HOME_ADVANTAGE

    # --- Goles: Poisson bivariante (modulado por la motivación) ---
    lam_goals_a = BASE_GOALS * att_a * def_b * home * mot_a
    lam_goals_b = BASE_GOALS * att_b * def_a * mot_b

    # --- Tensión del partido: mayor cuanto más igualado (y en eliminatorias) ---
    evenness = 1.0 - abs(sa - sb)            # 1 = idénticos, 0 = paliza
    tension = BASE_YELLOWS_TENSION + TENSION_MAX_BONUS * evenness
    if knockout:
        tension += KNOCKOUT_BONUS
    # un equipo necesitado de ganar mete más intensidad/tarjetas
    tension += 0.5 * max(mot_a - 1.0, mot_b - 1.0, 0.0)

    # --- Córners: se reparten según dominio ofensivo relativo ---
    share_a = (att_a ** CORNER_DOMINANCE) / (att_a ** CORNER_DOMINANCE + att_b ** CORNER_DOMINANCE)
    # ligero plus de córners totales para partidos abiertos entre buenos equipos
    intensity = 0.85 + 0.30 * ((sa + sb) / 2.0)
    total_corners = BASE_CORNERS * intensity
    lam_corners_a = total_corners * share_a
    lam_corners_b = total_corners * (1.0 - share_a)

    # --- Tarjetas: dominadas por el árbitro y moduladas por la tensión ---
    ref_yellow_factor = referee["yellows"] / AVG_YELLOWS
    total_yellows = AVG_YELLOWS * ref_yellow_factor * tension
    # el equipo más débil (más a la defensiva) tiende a recibir algo más
    disc_share_a = 0.5 - 0.12 * (sa - sb)
    lam_yellows_a = total_yellows * disc_share_a
    lam_yellows_b = total_yellows * (1.0 - disc_share_a)

    ref_red_factor = referee["reds"] / AVG_REDS
    lam_reds = AVG_REDS * ref_red_factor * tension

    ref_pen_factor = referee["penalties"] / AVG_PENALTIES
    lam_penalties = AVG_PENALTIES * ref_pen_factor

    return MatchLambdas(
        goals_a=lam_goals_a, goals_b=lam_goals_b,
        corners_a=lam_corners_a, corners_b=lam_corners_b,
        yellows_a=lam_yellows_a, yellows_b=lam_yellows_b,
        reds_total=lam_reds, penalties_total=lam_penalties,
        tension=tension,
    )
