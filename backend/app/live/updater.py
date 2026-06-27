"""Actualizador automático de designaciones arbitrales.

Lee el feed público de designaciones del Mundial 2026 (blog Law5-TheRef, que
publica los nombramientos oficiales de FIFA partido a partido), extrae para cada
encuentro el árbitro designado y lo guarda en los overrides. Si aparece un
árbitro que no está en el roster base, lo añade con datos estimados (marcado).

Es *best-effort* y tolerante a fallos: si la red falla o cambia el formato, no
rompe nada y conserva los overrides previos. Se ejecuta periódicamente desde el
backend y también bajo demanda vía /api/refresh.
"""

import re
import unicodedata
import urllib.request
from datetime import datetime, timezone

from ..data.referees import REFEREES_BY_ID
from ..data.tournament import FIXTURES
from . import store

# Pares de equipos (en ambos órdenes) de partidos aún por jugar de nuestro
# calendario. Solo aceptamos designaciones de estos para evitar ruido y basura.
_UPCOMING = set()
for _f in FIXTURES:
    a, b = _f.get("a"), _f.get("b")
    if isinstance(a, str) and isinstance(b, str) and len(a) == 3 and len(b) == 3:
        _UPCOMING.add((a, b))
        _UPCOMING.add((b, a))

FEED_URL = "http://law5-theref.blogspot.com/feeds/posts/default?alt=json&max-results=40"
_TIMEOUT = 20

# Nombre en MAYÚSCULAS (como aparece en el feed) -> código FIFA del dataset.
TEAM_CODES = {
    "MEXICO": "MEX", "SOUTH AFRICA": "RSA", "SOUTH KOREA": "KOR", "KOREA REPUBLIC": "KOR",
    "CZECHIA": "CZE", "CZECH REPUBLIC": "CZE", "SWITZERLAND": "SUI", "CANADA": "CAN",
    "BOSNIA AND HERZEGOVINA": "BIH", "BOSNIA": "BIH", "QATAR": "QAT", "BRAZIL": "BRA",
    "MOROCCO": "MAR", "SCOTLAND": "SCO", "HAITI": "HAI", "UNITED STATES": "USA", "USA": "USA",
    "AUSTRALIA": "AUS", "PARAGUAY": "PAR", "TURKIYE": "TUR", "TURKEY": "TUR", "GERMANY": "GER",
    "IVORY COAST": "CIV", "COTE D IVOIRE": "CIV", "ECUADOR": "ECU", "CURACAO": "CUW",
    "NETHERLANDS": "NED", "JAPAN": "JPN", "SWEDEN": "SWE", "TUNISIA": "TUN", "BELGIUM": "BEL",
    "EGYPT": "EGY", "IRAN": "IRN", "NEW ZEALAND": "NZL", "SPAIN": "ESP", "CAPE VERDE": "CPV",
    "URUGUAY": "URU", "SAUDI ARABIA": "SAU", "FRANCE": "FRA", "NORWAY": "NOR", "SENEGAL": "SEN",
    "IRAQ": "IRQ", "ARGENTINA": "ARG", "AUSTRIA": "AUT", "ALGERIA": "ALG", "JORDAN": "JOR",
    "COLOMBIA": "COL", "PORTUGAL": "POR", "DR CONGO": "COD", "CONGO DR": "COD", "CONGO": "COD",
    "UZBEKISTAN": "UZB", "ENGLAND": "ENG", "GHANA": "GHA", "CROATIA": "CRO", "PANAMA": "PAN",
}

# Código FIFA del árbitro -> país (para los descubiertos).
COUNTRY_BY_FIFA = {
    "POR": "Portugal", "MAR": "Marruecos", "BRA": "Brasil", "ITA": "Italia", "FRA": "Francia",
    "ESP": "España", "ENG": "Inglaterra", "GER": "Alemania", "NED": "Países Bajos",
    "ROU": "Rumanía", "SVN": "Eslovenia", "POL": "Polonia", "SWE": "Suecia", "SUI": "Suiza",
    "USA": "EE.UU.", "MEX": "México", "ARG": "Argentina", "BRA2": "Brasil", "QAT": "Catar",
    "AUS": "Australia", "IRN": "Irán", "CHN": "China", "JPN": "Japón", "UAE": "EAU",
    "KSA": "Arabia Saudí", "EGY": "Egipto", "DZA": "Argelia", "RSA": "Sudáfrica",
    "COL": "Colombia", "PER": "Perú", "CHI": "Chile", "URU": "Uruguay", "VEN": "Venezuela",
    "PAR": "Paraguay", "CRC": "Costa Rica", "SLV": "El Salvador", "HON": "Honduras",
    "JAM": "Jamaica", "CAN": "Canadá", "GAB": "Gabón", "MTN": "Mauritania", "UZB": "Uzbekistán",
    "JOR": "Jordania", "NZL": "Nueva Zelanda",
}

# Bloque: Match #NN ... EQUIPO A - EQUIPO B Referee: <nombre> Assistant Referee 1:
_BLOCK = re.compile(
    r"Match\s*#\d+.*?([A-Z][A-Z .'-]{1,24}?)\s*-\s*([A-Z][A-Z .'-]{1,24}?)\s*"
    r"Referee:\s*(.*?)\s*Assistant Referee 1:",
    re.S,
)


def _norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", s).strip().lower()


def _strip_html(html: str) -> str:
    text = re.sub(r"<[^>]+>", " ", html)
    text = re.sub(r"&[a-z]+;", " ", text)
    return re.sub(r"[ \t ]+", " ", text)


def _slug(name: str) -> str:
    return re.sub(r"[^a-z]", "", _norm(name).split(" ")[-1]) or _norm(name).replace(" ", "")


def _key(s: str) -> str:
    """Clave alfanumérica sin espacios ni signos (robusta a guiones/acentos)."""
    return re.sub(r"[^a-z]", "", _norm(s))


def _looks_like_name(name: str) -> bool:
    """Filtra basura de parseo: un nombre propio tiene >=2 palabras y minúsculas."""
    parts = name.split()
    if len(parts) < 2:
        return False
    if name == name.upper():            # todo mayúsculas -> no es nombre
        return False
    if any(ch.isdigit() for ch in name):
        return False
    return True


def _match_referee(name: str, fifa: str | None):
    """Devuelve (ref_id, nuevo_ref|None) para un nombre de árbitro del feed."""
    nk = _key(name)
    nlast = _norm(name).replace("-", " ").split(" ")[-1]
    for rid, r in REFEREES_BY_ID.items():
        if _key(r["name"]) == nk:
            return rid, None
    for rid, r in REFEREES_BY_ID.items():
        rlast = _norm(r["name"]).replace("-", " ").split(" ")[-1]
        if len(nlast) > 3 and rlast == nlast:
            return rid, None
    # No está en el roster: lo añadimos con datos estimados.
    rid = _slug(name)
    new = {
        "id": rid, "name": name.strip(),
        "country": COUNTRY_BY_FIFA.get(fifa or "", fifa or "—"),
        "confed": "—", "yellows": 4.0, "reds": 0.18, "penalties": 0.28,
        "fouls": None, "matches": None, "style": "Equilibrado", "estimated": True,
    }
    return rid, new


def _fetch_entries():
    req = urllib.request.Request(FEED_URL, headers={"User-Agent": "Mozilla/5.0"})
    import json
    with urllib.request.urlopen(req, timeout=_TIMEOUT) as resp:
        data = json.load(resp)
    return data.get("feed", {}).get("entry", [])


def refresh() -> dict:
    """Busca designaciones nuevas y las vuelca a los overrides."""
    try:
        entries = _fetch_entries()
    except Exception as ex:  # red caída, formato cambiado, etc.
        return {"ok": False, "error": str(ex)}

    appointments: dict[str, str] = {}
    new_refs: dict[str, dict] = {}
    for e in entries:
        html = e.get("content", {}).get("$t", "")
        text = _strip_html(html)
        for ta, tb, refblob in _BLOCK.findall(text):
            ref = refblob.strip()
            if len(ref) < 3:
                continue  # aún sin designar
            # Quita los códigos de país finales (p. ej. "POR", "AUS/IRN").
            toks = ref.split()
            fifa = None
            while toks and re.fullmatch(r"[A-Z]{2,}(?:/[A-Z]{2,})*", toks[-1]):
                if fifa is None:
                    fifa = toks[-1].split("/")[0]
                toks.pop()
            name = " ".join(toks)
            ca = TEAM_CODES.get(ta.strip())
            cb = TEAM_CODES.get(tb.strip())
            if not ca or not cb:
                continue
            if (ca, cb) not in _UPCOMING:        # solo partidos de nuestro calendario
                continue
            if not _looks_like_name(name):       # descarta basura de parseo
                continue
            rid, new = _match_referee(name, fifa)
            if new:
                new_refs[rid] = new
            appointments[f"{ca}-{cb}"] = rid

    try:
        data = store.load()
        data["appointments"].update(appointments)
        data["referees"].update(new_refs)
        data["updated"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
        store.save(data)
    except Exception as ex:  # p. ej. Supabase inaccesible
        return {"ok": False, "error": f"store: {ex}"}
    return {
        "ok": True, "updated": data["updated"],
        "appointments_found": len(appointments),
        "new_referees": len(new_refs),
        "appointments": appointments,
    }
