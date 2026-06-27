"""Selecciones REALES del Mundial 2026 (Canadá · México · EE. UU.).

48 equipos repartidos en 12 grupos (A-L). Para cada selección se guarda un
rating tipo Elo futbolístico (pre-torneo, escala World Football Elo) del que se
derivan los parámetros de ataque/defensa del modelo de Poisson. El rendimiento
DENTRO del torneo se incorpora aparte (ver ``tournament.py``: clasificaciones y
ajuste por forma), de modo que el predictor combina nivel histórico + forma real.

Fuente de la composición de grupos: sorteo final y clasificaciones reales del
torneo (datos en vivo). Los Elo son representativos y reemplazables por un feed.

Campos: code · name · conf · elo (pre-torneo) · flag · group
"""

TEAMS = [
    # Grupo A
    {"code": "MEX", "name": "México",            "conf": "CONCACAF", "elo": 1790, "flag": "🇲🇽", "group": "A"},
    {"code": "RSA", "name": "Sudáfrica",         "conf": "CAF",      "elo": 1610, "flag": "🇿🇦", "group": "A"},
    {"code": "KOR", "name": "Corea del Sur",     "conf": "AFC",      "elo": 1740, "flag": "🇰🇷", "group": "A"},
    {"code": "CZE", "name": "Chequia",           "conf": "UEFA",     "elo": 1715, "flag": "🇨🇿", "group": "A"},
    # Grupo B
    {"code": "SUI", "name": "Suiza",             "conf": "UEFA",     "elo": 1835, "flag": "🇨🇭", "group": "B"},
    {"code": "CAN", "name": "Canadá",            "conf": "CONCACAF", "elo": 1730, "flag": "🇨🇦", "group": "B"},
    {"code": "BIH", "name": "Bosnia y Herzeg.",  "conf": "UEFA",     "elo": 1680, "flag": "🇧🇦", "group": "B"},
    {"code": "QAT", "name": "Catar",             "conf": "AFC",      "elo": 1680, "flag": "🇶🇦", "group": "B"},
    # Grupo C
    {"code": "BRA", "name": "Brasil",            "conf": "CONMEBOL", "elo": 2000, "flag": "🇧🇷", "group": "C"},
    {"code": "MAR", "name": "Marruecos",         "conf": "CAF",      "elo": 1840, "flag": "🇲🇦", "group": "C"},
    {"code": "SCO", "name": "Escocia",           "conf": "UEFA",     "elo": 1700, "flag": "🏴󠁧󠁢󠁳󠁣󠁴󠁿", "group": "C"},
    {"code": "HAI", "name": "Haití",             "conf": "CONCACAF", "elo": 1500, "flag": "🇭🇹", "group": "C"},
    # Grupo D
    {"code": "USA", "name": "Estados Unidos",    "conf": "CONCACAF", "elo": 1800, "flag": "🇺🇸", "group": "D"},
    {"code": "AUS", "name": "Australia",         "conf": "AFC",      "elo": 1715, "flag": "🇦🇺", "group": "D"},
    {"code": "PAR", "name": "Paraguay",          "conf": "CONMEBOL", "elo": 1700, "flag": "🇵🇾", "group": "D"},
    {"code": "TUR", "name": "Turquía",           "conf": "UEFA",     "elo": 1770, "flag": "🇹🇷", "group": "D"},
    # Grupo E
    {"code": "GER", "name": "Alemania",          "conf": "UEFA",     "elo": 1930, "flag": "🇩🇪", "group": "E"},
    {"code": "CIV", "name": "Costa de Marfil",   "conf": "CAF",      "elo": 1715, "flag": "🇨🇮", "group": "E"},
    {"code": "ECU", "name": "Ecuador",           "conf": "CONMEBOL", "elo": 1765, "flag": "🇪🇨", "group": "E"},
    {"code": "CUW", "name": "Curazao",           "conf": "CONCACAF", "elo": 1490, "flag": "🇨🇼", "group": "E"},
    # Grupo F
    {"code": "NED", "name": "Países Bajos",      "conf": "UEFA",     "elo": 1985, "flag": "🇳🇱", "group": "F"},
    {"code": "JPN", "name": "Japón",             "conf": "AFC",      "elo": 1840, "flag": "🇯🇵", "group": "F"},
    {"code": "SWE", "name": "Suecia",            "conf": "UEFA",     "elo": 1760, "flag": "🇸🇪", "group": "F"},
    {"code": "TUN", "name": "Túnez",             "conf": "CAF",      "elo": 1685, "flag": "🇹🇳", "group": "F"},
    # Grupo G
    {"code": "BEL", "name": "Bélgica",           "conf": "UEFA",     "elo": 1940, "flag": "🇧🇪", "group": "G"},
    {"code": "EGY", "name": "Egipto",            "conf": "CAF",      "elo": 1715, "flag": "🇪🇬", "group": "G"},
    {"code": "IRN", "name": "Irán",              "conf": "AFC",      "elo": 1730, "flag": "🇮🇷", "group": "G"},
    {"code": "NZL", "name": "Nueva Zelanda",     "conf": "OFC",      "elo": 1505, "flag": "🇳🇿", "group": "G"},
    # Grupo H
    {"code": "ESP", "name": "España",            "conf": "UEFA",     "elo": 2095, "flag": "🇪🇸", "group": "H"},
    {"code": "CPV", "name": "Cabo Verde",        "conf": "CAF",      "elo": 1560, "flag": "🇨🇻", "group": "H"},
    {"code": "URU", "name": "Uruguay",           "conf": "CONMEBOL", "elo": 1875, "flag": "🇺🇾", "group": "H"},
    {"code": "SAU", "name": "Arabia Saudí",      "conf": "AFC",      "elo": 1650, "flag": "🇸🇦", "group": "H"},
    # Grupo I
    {"code": "FRA", "name": "Francia",           "conf": "UEFA",     "elo": 2090, "flag": "🇫🇷", "group": "I"},
    {"code": "NOR", "name": "Noruega",           "conf": "UEFA",     "elo": 1820, "flag": "🇳🇴", "group": "I"},
    {"code": "SEN", "name": "Senegal",           "conf": "CAF",      "elo": 1800, "flag": "🇸🇳", "group": "I"},
    {"code": "IRQ", "name": "Irak",              "conf": "AFC",      "elo": 1560, "flag": "🇮🇶", "group": "I"},
    # Grupo J
    {"code": "ARG", "name": "Argentina",         "conf": "CONMEBOL", "elo": 2130, "flag": "🇦🇷", "group": "J"},
    {"code": "AUT", "name": "Austria",           "conf": "UEFA",     "elo": 1790, "flag": "🇦🇹", "group": "J"},
    {"code": "ALG", "name": "Argelia",           "conf": "CAF",      "elo": 1740, "flag": "🇩🇿", "group": "J"},
    {"code": "JOR", "name": "Jordania",          "conf": "AFC",      "elo": 1560, "flag": "🇯🇴", "group": "J"},
    # Grupo K
    {"code": "COL", "name": "Colombia",          "conf": "CONMEBOL", "elo": 1860, "flag": "🇨🇴", "group": "K"},
    {"code": "POR", "name": "Portugal",          "conf": "UEFA",     "elo": 1990, "flag": "🇵🇹", "group": "K"},
    {"code": "COD", "name": "RD Congo",          "conf": "CAF",      "elo": 1640, "flag": "🇨🇩", "group": "K"},
    {"code": "UZB", "name": "Uzbekistán",        "conf": "AFC",      "elo": 1605, "flag": "🇺🇿", "group": "K"},
    # Grupo L
    {"code": "ENG", "name": "Inglaterra",        "conf": "UEFA",     "elo": 2010, "flag": "🏴󠁧󠁢󠁥󠁮󠁧󠁿", "group": "L"},
    {"code": "GHA", "name": "Ghana",             "conf": "CAF",      "elo": 1685, "flag": "🇬🇭", "group": "L"},
    {"code": "CRO", "name": "Croacia",           "conf": "UEFA",     "elo": 1880, "flag": "🇭🇷", "group": "L"},
    {"code": "PAN", "name": "Panamá",            "conf": "CONCACAF", "elo": 1660, "flag": "🇵🇦", "group": "L"},
]

TEAMS_BY_CODE = {t["code"]: t for t in TEAMS}

ELO_MIN = 1450.0
ELO_MAX = 2150.0


def team_strength(team: dict) -> float:
    """Fuerza normalizada en [0, 1] a partir del Elo (efectivo si trae forma)."""
    s = (team["elo"] - ELO_MIN) / (ELO_MAX - ELO_MIN)
    return max(0.0, min(1.0, s))
