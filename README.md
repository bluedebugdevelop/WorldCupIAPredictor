# WorldCupIAPredictor ⚽🤖

Motor predictivo para el **Mundial 2026**. Estima, para cualquier emparejamiento,
el resultado (1X2), los goles, los córners, las tarjetas y el impacto del árbitro,
mediante un **modelo de Poisson bivariante** y **simulación Monte Carlo**.

![stack](https://img.shields.io/badge/backend-FastAPI-009688) ![stack](https://img.shields.io/badge/engine-NumPy%20Monte%20Carlo-013243) ![stack](https://img.shields.io/badge/frontend-Vanilla%20JS-f7df1e)

## Datos reales del Mundial 2026

La app está cargada con el **estado real del torneo** (Canadá · México · EE. UU.):

- **Grupos (A–L)** con las 48 selecciones reales y su **clasificación real** de la
  fase de grupos (PJ, G, E, P, diferencia de goles, puntos).
- **Calendario real de la Ronda de 32** con fecha, hora, zona horaria y sede de
  cada cruce; desde cada partido definido se puede lanzar la predicción con un clic.
- **Forma en el torneo**: el predictor ajusta el Elo de cada selección según su
  rendimiento real (puntos y diferencia de goles por partido), de modo que combina
  *nivel histórico* + *cómo está llegando el equipo*.
- **Calendario unificado y cronológico** (hora de España): última jornada de la
  fase de grupos (grupos J, K, L) + Ronda de 32, ordenado por los próximos partidos.
- **Árbitros reales**: roster de colegiados designados por FIFA para el Mundial
  2026 con sus **estadísticas reales** (amarillas, rojas y faltas por partido, y
  partidos dirigidos). Cada partido muestra su **árbitro designado real** (cuando
  está publicado) y el predictor lo autoselecciona y usa sus medias para estimar
  tarjetas y penaltis.
- **Actualización automática de designaciones**: el backend consulta el feed
  oficial de nombramientos (Law5-TheRef, que publica las designaciones de FIFA
  partido a partido) **al arrancar y cada 3 horas**, y vuelca las nuevas
  designaciones a `data/live_overrides.json`. Cuando aparece un árbitro que no
  está en el roster, se añade con datos estimados (marcado «est.»). El calendario
  muestra la hora de la última sincronización y un botón **«Actualizar
  designaciones»** para forzarla. Endpoints: `POST /api/refresh`, `GET /api/status`.
  Implementado en `backend/app/live/` (sin dependencias externas: usa la librería
  estándar).
- **Intereses de cada equipo**: en la última jornada de grupos se calcula qué
  necesita cada selección (clasificado · le vale el empate · necesita ganar ·
  eliminado) resolviendo todos los escenarios de la jornada. El predictor aplica
  un multiplicador de motivación: el que necesita ganar empuja más (más ataque y
  tarjetas); el ya clasificado o eliminado rinde algo por debajo.

> Los datos se obtuvieron de fuentes en vivo (clasificaciones y calendario
> oficiales) y viven en `backend/app/data/tournament.py`. Para refrescarlos basta
> con actualizar ese archivo (o conectarlo a una API en tiempo real).

## Qué predice

- **Resultado 1X2**: probabilidad de victoria de cada selección y empate.
- **Goles**: goles esperados (xG) por equipo, marcadores más probables, BTTS y over/under 1.5/2.5/3.5.
- **Córners**: media por equipo y total, over 9.5 / 10.5.
- **Tarjetas y penaltis**: amarillas por equipo, probabilidad de roja y de penalti — **escalados por el perfil del árbitro**.
- **Eliminatoria**: probabilidad de pasar de ronda incluyendo prórroga/penaltis.

## Metodología (resumen para la memoria)

El núcleo del motor vive en `backend/app/engine/`:

1. **`model.py` — parte determinista.** Cada selección tiene un rating tipo *Elo
   futbolístico* del que se derivan factores multiplicativos de ataque y defensa
   (`exp(±k·(fuerza−0.5))`). Con ellos se calculan las medias λ de Poisson para
   los goles de cada equipo, aplicando ventaja de campo si la sede no es neutral.
   Los córners se reparten según el dominio ofensivo relativo y las tarjetas se
   centran en la **media histórica del árbitro**, moduladas por un *índice de
   tensión* (los partidos igualados y las eliminatorias generan más tarjetas).

2. **`simulate.py` — parte estocástica.** Se muestrean N partidos completos
   (por defecto 20 000) extrayendo goles, córners, tarjetas, rojas y penaltis de
   sus respectivas distribuciones de Poisson (vectorizado con NumPy). Los
   resultados se agregan en probabilidades y valores esperados.

El modelo de Poisson bivariante para goles es el estándar académico en
predicción de fútbol (Maher, 1982; Dixon & Coles, 1997) y la base de modelos
públicos como el *Soccer Power Index* de FiveThirtyEight.

> **Nota de alcance.** Los ratings de selecciones y los perfiles de árbitros son
> valores representativos curados, no un feed en vivo. La arquitectura está
> preparada para sustituirlos por datos reales (FIFA/Elo, Opta, Transfermarkt)
> sin tocar el motor: basta con alimentar `data/teams.py` y `data/referees.py`
> manteniendo las mismas claves.

## Arquitectura

```
WorldCupIAPredictor/
├── backend/
│   ├── app/
│   │   ├── main.py            # API FastAPI + sirve el frontend
│   │   ├── schemas.py         # validación de peticiones (Pydantic)
│   │   ├── data/
│   │   │   ├── teams.py       # 48 selecciones con rating Elo
│   │   │   └── referees.py    # 12 árbitros con medias de tarjetas/penaltis
│   │   └── engine/
│   │       ├── model.py       # cálculo de las medias λ (Poisson)
│   │       └── simulate.py    # simulación Monte Carlo
│   └── requirements.txt
├── frontend/                  # interfaz web (HTML + CSS + JS, sin framework)
│   ├── index.html
│   ├── styles.css
│   └── app.js
├── run.ps1                    # arranque en Windows
└── run.sh                     # arranque en Linux/macOS
```

## Puesta en marcha

### Windows (PowerShell)
```powershell
cd WorldCupIAPredictor
./run.ps1
```

### Linux / macOS
```bash
cd WorldCupIAPredictor
./run.sh
```

El script crea el entorno virtual, instala dependencias y arranca el servidor.
Después abre <http://127.0.0.1:8000>.

> Arranque manual:
> ```bash
> cd backend
> python -m venv .venv && .venv\Scripts\activate   # (source .venv/bin/activate en Linux/macOS)
> pip install -r requirements.txt
> uvicorn app.main:app --reload
> ```

## API

| Método | Ruta            | Descripción                                   |
|--------|-----------------|-----------------------------------------------|
| GET    | `/api/teams`    | Catálogo de selecciones (ordenado por Elo)    |
| GET    | `/api/referees` | Catálogo de árbitros                          |
| POST   | `/api/predict`  | Ejecuta la simulación de un emparejamiento    |

Ejemplo de `POST /api/predict`:
```json
{
  "team_a": "ARG", "team_b": "FRA", "referee": "orsato",
  "neutral": true, "knockout": true, "n_sims": 20000
}
```

Documentación interactiva automática en <http://127.0.0.1:8000/docs>.

## Despliegue (Vercel + Supabase)

La app está lista para producción serverless. El backend FastAPI corre como
función Python en Vercel, el frontend se sirve igual, y el estado en vivo
(designaciones) se guarda en Supabase (el disco de Vercel es efímero).

### 1. Supabase
1. Crea un proyecto en <https://supabase.com>.
2. En **SQL Editor**, ejecuta `supabase/schema.sql` (crea la tabla `kv_store`).
3. En **Project Settings → API**, copia:
   - `Project URL` → será `SUPABASE_URL`
   - `service_role` key (secreta) → será `SUPABASE_SERVICE_KEY`

### 2. Vercel
1. En <https://vercel.com>, **Add New → Project → Import** el repo
   `bluedebugdevelop/WorldCupIAPredictor`.
2. Framework preset: **Other** (lo gobierna `vercel.json`). No hace falta build command.
3. En **Settings → Environment Variables**, añade:
   - `SUPABASE_URL` = la URL del proyecto
   - `SUPABASE_SERVICE_KEY` = la service_role key
4. **Deploy**. Vercel detecta `api/index.py` (la app ASGI) y sirve todo.
5. El **cron** de `vercel.json` llama a `/api/refresh` cada 3 h para traer las
   designaciones nuevas. Puedes forzarlo desde el botón «Actualizar» de la app.

Cada `git push` a `main` vuelve a desplegar automáticamente.

> **Local vs producción**: sin variables de Supabase, el almacén usa el fichero
> `backend/app/data/live_overrides.json` (modo desarrollo). Con ellas, usa
> Supabase. El mismo código sirve para ambos.
