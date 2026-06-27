"""Árbitros REALES del Mundial 2026 con sus estadísticas reales.

FIFA designó 52 árbitros para el torneo (9 abr 2026). Aquí se recogen los más
relevantes con sus estadísticas reales de disciplina (amarillas, rojas y faltas
por partido, y partidos dirigidos) tomadas de su historial en competiciones de
élite. El árbitro es un factor de primer orden en la predicción de tarjetas y
penaltis: el motor escala las distribuciones según estas medias.

Campos: id · name · country · confed · yellows · reds · penalties · fouls ·
matches · style

Nota: ``yellows``/``reds``/``fouls``/``matches`` son cifras medidas (historial).
``penalties`` es una estimación por estilo (no siempre publicada). Para datos del
propio Mundial basta con refrescar estos valores desde un feed.
"""

REFEREES = [
    {"id": "marciniak", "name": "Szymon Marciniak",        "country": "Polonia",    "confed": "UEFA",     "yellows": 4.3, "reds": 0.13, "penalties": 0.26, "fouls": 24.0, "matches": 215, "style": "Estricto"},
    {"id": "turpin",    "name": "Clément Turpin",          "country": "Francia",    "confed": "UEFA",     "yellows": 3.2, "reds": 0.23, "penalties": 0.30, "fouls": 22.5, "matches": 205, "style": "Permite jugar"},
    {"id": "kovacs",    "name": "István Kovács",           "country": "Rumanía",    "confed": "UEFA",     "yellows": 5.0, "reds": 0.26, "penalties": 0.31, "fouls": 25.3, "matches": 197, "style": "Muy estricto"},
    {"id": "faghani",   "name": "Alireza Faghani",         "country": "Australia",  "confed": "AFC",      "yellows": 3.7, "reds": 0.11, "penalties": 0.27, "fouls": 19.7, "matches": 141, "style": "Equilibrado"},
    {"id": "aljassim",  "name": "Abdulrahman Al-Jassim",   "country": "Catar",      "confed": "AFC",      "yellows": 4.3, "reds": 0.24, "penalties": 0.30, "fouls": 22.8, "matches": 108, "style": "Estricto"},
    {"id": "sampaio",   "name": "Wilton Sampaio",          "country": "Brasil",     "confed": "CONMEBOL", "yellows": 4.8, "reds": 0.23, "penalties": 0.34, "fouls": 25.8, "matches": 222, "style": "Muy estricto"},
    {"id": "ramos",     "name": "César Arturo Ramos",      "country": "México",     "confed": "CONCACAF", "yellows": 4.4, "reds": 0.41, "penalties": 0.35, "fouls": 23.5, "matches": 174, "style": "Muy estricto"},
    {"id": "vincic",    "name": "Slavko Vinčić",           "country": "Eslovenia",  "confed": "UEFA",     "yellows": 3.9, "reds": 0.12, "penalties": 0.28, "fouls": 25.4, "matches": 90,  "style": "Equilibrado"},
    {"id": "oliver",    "name": "Michael Oliver",          "country": "Inglaterra", "confed": "UEFA",     "yellows": 3.7, "reds": 0.14, "penalties": 0.25, "fouls": 22.8, "matches": 252, "style": "Permite jugar"},
    {"id": "taylor",    "name": "Anthony Taylor",          "country": "Inglaterra", "confed": "UEFA",     "yellows": 3.9, "reds": 0.16, "penalties": 0.26, "fouls": 21.4, "matches": 264, "style": "Equilibrado"},
    {"id": "makkelie",  "name": "Danny Makkelie",          "country": "Países Bajos","confed": "UEFA",    "yellows": 3.4, "reds": 0.15, "penalties": 0.26, "fouls": 22.3, "matches": 255, "style": "Permite jugar"},
    {"id": "letexier",  "name": "François Letexier",       "country": "Francia",    "confed": "UEFA",     "yellows": 3.6, "reds": 0.14, "penalties": 0.27, "fouls": 21.0, "matches": 160, "style": "Equilibrado"},
    {"id": "pinheiro",  "name": "João Pinheiro",           "country": "Portugal",   "confed": "UEFA",     "yellows": 4.5, "reds": 0.18, "penalties": 0.29, "fouls": 24.0, "matches": 180, "style": "Estricto"},
    {"id": "zwayer",    "name": "Felix Zwayer",            "country": "Alemania",   "confed": "UEFA",     "yellows": 4.1, "reds": 0.16, "penalties": 0.28, "fouls": 23.0, "matches": 200, "style": "Estricto"},
    {"id": "nyberg",    "name": "Glenn Nyberg",            "country": "Suecia",     "confed": "UEFA",     "yellows": 3.8, "reds": 0.13, "penalties": 0.27, "fouls": 21.5, "matches": 130, "style": "Equilibrado"},
    {"id": "tello",     "name": "Facundo Tello",           "country": "Argentina",  "confed": "CONMEBOL", "yellows": 5.2, "reds": 0.35, "penalties": 0.33, "fouls": 26.0, "matches": 150, "style": "Muy estricto"},
    {"id": "elfath",    "name": "Ismail Elfath",           "country": "EE.UU.",     "confed": "CONCACAF", "yellows": 3.9, "reds": 0.15, "penalties": 0.28, "fouls": 22.0, "matches": 140, "style": "Equilibrado"},
    {"id": "ghorbal",   "name": "Mustapha Ghorbal",        "country": "Argelia",    "confed": "CAF",      "yellows": 4.2, "reds": 0.20, "penalties": 0.30, "fouls": 23.5, "matches": 120, "style": "Estricto"},
    {"id": "fischer",   "name": "Drew Fischer",            "country": "Canadá",     "confed": "CONCACAF", "yellows": 3.8, "reds": 0.16, "penalties": 0.28, "fouls": 21.0, "matches": 110, "style": "Equilibrado"},
]

REFEREES_BY_ID = {r["id"]: r for r in REFEREES}

# Medias de referencia de un Mundial (para el factor relativo del árbitro).
AVG_YELLOWS = 4.0
AVG_REDS = 0.18
AVG_PENALTIES = 0.28
