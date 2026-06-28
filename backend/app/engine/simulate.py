"""Simulación Monte Carlo del partido.

Dadas las medias (lambda) del modelo, muestrea N partidos completos y agrega los
resultados en probabilidades y valores esperados. Vectorizado con NumPy: 20.000
simulaciones se resuelven en milisegundos.

Lo que produce:
  - 1X2 (victoria local / empate / victoria visitante)
  - distribución de marcadores y resultados más probables
  - goles esperados (xG del modelo), ambos marcan, over/under
  - córners esperados y over/under de córners
  - tarjetas (amarillas por equipo, rojas), penaltis
  - probabilidad de prórroga/penaltis si es eliminatoria
"""

from collections import Counter

import numpy as np

from .model import compute_lambdas, MatchLambdas


def _poisson(rng, lam: float, n: int) -> np.ndarray:
    return rng.poisson(max(lam, 1e-6), n)


def simulate(team_a: dict, team_b: dict, referee: dict,
             neutral: bool = True, knockout: bool = False,
             mot_a: float = 1.0, mot_b: float = 1.0,
             n_sims: int = 20000, seed: int | None = None) -> dict:
    """Ejecuta la simulación y devuelve un diccionario serializable."""
    rng = np.random.default_rng(seed)
    lam = compute_lambdas(team_a, team_b, referee, neutral=neutral, knockout=knockout,
                          mot_a=mot_a, mot_b=mot_b)

    # --- Goles ---
    ga = _poisson(rng, lam.goals_a, n_sims)
    gb = _poisson(rng, lam.goals_b, n_sims)

    a_win = float(np.mean(ga > gb))
    draw = float(np.mean(ga == gb))
    b_win = float(np.mean(ga < gb))

    total_goals = ga + gb
    btts = float(np.mean((ga > 0) & (gb > 0)))
    over25 = float(np.mean(total_goals > 2.5))
    over15 = float(np.mean(total_goals > 1.5))
    over35 = float(np.mean(total_goals > 3.5))

    # Marcadores más probables (cap a 6 para una distribución legible)
    capped = [(min(int(x), 6), min(int(y), 6)) for x, y in zip(ga, gb)]
    score_counts = Counter(capped)
    top_scores = [
        {"score": f"{s[0]}-{s[1]}", "prob": round(c / n_sims, 4)}
        for s, c in score_counts.most_common(6)
    ]

    # --- Córners ---
    ca = _poisson(rng, lam.corners_a, n_sims)
    cb = _poisson(rng, lam.corners_b, n_sims)
    total_corners = ca + cb
    corners_over_95 = float(np.mean(total_corners > 9.5))
    corners_over_105 = float(np.mean(total_corners > 10.5))

    # --- Tarjetas y penaltis ---
    ya = _poisson(rng, lam.yellows_a, n_sims)
    yb = _poisson(rng, lam.yellows_b, n_sims)
    reds = _poisson(rng, lam.reds_total, n_sims)
    pens = _poisson(rng, lam.penalties_total, n_sims)
    total_cards = ya + yb
    cards_over_45 = float(np.mean(total_cards > 4.5))
    red_prob = float(np.mean(reds > 0))
    pen_prob = float(np.mean(pens > 0))

    # --- Eliminatoria: probabilidad de pasar (incluye prórroga/penaltis) ---
    knockout_block = None
    if knockout:
        decided = ga != gb
        a_adv = a_win  # ya resuelto en 90'
        b_adv = b_win
        # los empates se resuelven; con ligera ventaja al equipo más fuerte
        draw_mask = ~decided
        n_draw = int(np.sum(draw_mask))
        if n_draw:
            # probabilidad de que A gane la tanda en función de su fuerza relativa
            pa = 0.5 + 0.5 * (lam.goals_a - lam.goals_b) / max(lam.goals_a + lam.goals_b, 1e-6)
            pa = min(max(pa, 0.2), 0.8)
            a_extra = (n_draw * pa) / n_sims
            b_extra = (n_draw * (1 - pa)) / n_sims
        else:
            a_extra = b_extra = 0.0
        knockout_block = {
            "advance_a": round(a_adv + a_extra, 4),
            "advance_b": round(b_adv + b_extra, 4),
            "to_extra_time": round(draw, 4),
        }

    return {
        "teams": {
            "a": {"code": team_a["code"], "name": team_a["name"], "flag": team_a["flag"],
                  "iso": team_a.get("iso", ""),
                  "elo": round(team_a["elo"]), "elo_base": round(team_a.get("elo_base", team_a["elo"])),
                  "form_delta": team_a.get("form_delta", 0), "stake": team_a.get("stake")},
            "b": {"code": team_b["code"], "name": team_b["name"], "flag": team_b["flag"],
                  "iso": team_b.get("iso", ""),
                  "elo": round(team_b["elo"]), "elo_base": round(team_b.get("elo_base", team_b["elo"])),
                  "form_delta": team_b.get("form_delta", 0), "stake": team_b.get("stake")},
        },
        "referee": {"name": referee["name"], "country": referee["country"], "style": referee["style"],
                    "yellows": referee["yellows"], "reds": referee["reds"], "penalties": referee["penalties"],
                    "fouls": referee.get("fouls"), "matches": referee.get("matches")},
        "config": {"neutral": neutral, "knockout": knockout, "n_sims": n_sims},
        "outcome": {
            "a_win": round(a_win, 4),
            "draw": round(draw, 4),
            "b_win": round(b_win, 4),
        },
        "goals": {
            "xg_a": round(float(lam.goals_a), 2),
            "xg_b": round(float(lam.goals_b), 2),
            "avg_a": round(float(np.mean(ga)), 2),
            "avg_b": round(float(np.mean(gb)), 2),
            "btts": round(btts, 4),
            "over_15": round(over15, 4),
            "over_25": round(over25, 4),
            "over_35": round(over35, 4),
            "top_scores": top_scores,
        },
        "corners": {
            "avg_a": round(float(np.mean(ca)), 1),
            "avg_b": round(float(np.mean(cb)), 1),
            "avg_total": round(float(np.mean(total_corners)), 1),
            "over_95": round(corners_over_95, 4),
            "over_105": round(corners_over_105, 4),
        },
        "possession": {
            "a": round(lam.possession_a * 100),
            "b": round((1 - lam.possession_a) * 100),
        },
        "cards": {
            "yellows_a": round(float(np.mean(ya)), 2),
            "yellows_b": round(float(np.mean(yb)), 2),
            "yellows_total": round(float(np.mean(total_cards)), 2),
            "over_45": round(cards_over_45, 4),
            "red_prob": round(red_prob, 4),
            "pen_prob": round(pen_prob, 4),
            "tension": round(float(lam.tension), 2),
        },
        "knockout": knockout_block,
    }
