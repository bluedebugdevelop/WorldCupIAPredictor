/* WorldCupIAPredictor — frontend con datos reales del Mundial 2026 */

const API = "";
const $ = (id) => document.getElementById(id);
const pct = (x) => `${(x * 100).toFixed(1)}%`;
const icons = () => { if (window.lucide) lucide.createIcons(); };
const fi = (iso) => (iso ? `fi fi-${iso}` : "");

let TEAMS = [], REFEREES = [];

async function boot() {
  try {
    [TEAMS, REFEREES] = await Promise.all([
      fetch(`${API}/api/teams`).then((r) => r.json()),
      fetch(`${API}/api/referees`).then((r) => r.json()),
    ]);
  } catch (e) {
    $("emptyState").innerHTML =
      `<h3>No se pudo conectar con el motor</h3><p>Arranca el backend con <code>uvicorn app.main:app</code></p>`;
    return;
  }

  fillTeamSelect("teamA", "ESP");
  fillTeamSelect("teamB", "BRA");
  fillRefSelect();
  updateFlags(); updateRefMeta();

  $("teamA").addEventListener("change", updateFlags);
  $("teamB").addEventListener("change", updateFlags);
  $("referee").addEventListener("change", updateRefMeta);
  $("sims").addEventListener("input", (e) => {
    $("simsVal").textContent = Number(e.target.value).toLocaleString("es-ES");
  });
  $("runBtn").addEventListener("click", run);

  document.querySelectorAll(".tab").forEach((t) =>
    t.addEventListener("click", () => switchTab(t.dataset.tab)));

  loadGroups();
  loadSchedule();
  loadStatus();

  $("refreshBtn").addEventListener("click", async () => {
    const btn = $("refreshBtn");
    btn.disabled = true; btn.innerHTML = `<i data-lucide="loader"></i> Actualizando…`; icons();
    try {
      await fetch(`${API}/api/refresh`, { method: "POST" });
      await Promise.all([loadSchedule(), loadStatus(), fillRefSelectKeep()]);
    } catch (e) { /* noop */ }
    btn.disabled = false; btn.innerHTML = `<i data-lucide="refresh-cw"></i> Actualizar designaciones`; icons();
  });

  icons();
}

async function loadStatus() {
  try {
    const s = await fetch(`${API}/api/status`).then((r) => r.json());
    const el = $("syncStatus");
    if (s.updated) {
      const d = new Date(s.updated).toLocaleString("es-ES", { day: "numeric", month: "short", hour: "2-digit", minute: "2-digit" });
      el.innerHTML = `Última actualización: <strong>${d}</strong> · ${s.appointments} designaciones`;
    } else {
      el.textContent = "Sin sincronizar todavía";
    }
  } catch (e) { $("syncStatus").textContent = "Sin conexión con el motor"; }
}

async function fillRefSelectKeep() {
  const cur = $("referee").value;
  REFEREES = await fetch(`${API}/api/referees`).then((r) => r.json());
  fillRefSelect();
  if (REFEREES.some((r) => r.id === cur)) $("referee").value = cur;
  updateRefMeta();
}

function switchTab(name) {
  document.querySelectorAll(".tab").forEach((t) => t.classList.toggle("active", t.dataset.tab === name));
  document.querySelectorAll(".view").forEach((v) => v.classList.add("hidden"));
  $(`view-${name}`).classList.remove("hidden");
}

/* ---------- Predictor ---------- */
function fillTeamSelect(id, defCode) {
  const sorted = [...TEAMS].sort((a, b) => a.name.localeCompare(b.name, "es"));
  $(id).innerHTML = sorted.map(
    (t) => `<option value="${t.code}" ${t.code === defCode ? "selected" : ""}>${t.name} · Gr.${t.group}</option>`
  ).join("");
}
function fillRefSelect() {
  $("referee").innerHTML = REFEREES.map((r) => `<option value="${r.id}">${r.name} (${r.country})${r.estimated ? " ·est" : ""}</option>`).join("");
}
const teamByCode = (c) => TEAMS.find((t) => t.code === c);
function setFlag(id, code) {
  const t = teamByCode(code);
  $(id).className = `flag-el ${fi(t?.iso)}`;
}
function updateFlags() { setFlag("flagA", $("teamA").value); setFlag("flagB", $("teamB").value); }
function updateRefMeta() {
  const r = REFEREES.find((x) => x.id === $("referee").value);
  if (!r) return;
  const extra = r.matches ? ` · ${r.fouls} faltas/p · ${r.matches} partidos` : (r.estimated ? " · datos estimados" : "");
  $("refMeta").textContent = `${r.style} · ${r.yellows} amar. ${r.reds} rojas ${r.penalties} pen/p${extra}`;
}

async function run() {
  const btn = $("runBtn");
  if ($("teamA").value === $("teamB").value) return flashError("Elige dos selecciones distintas.");
  btn.classList.add("loading");
  btn.querySelector(".btn-text").innerHTML = `<span class="spinner"></span>Simulando…`;
  try {
    const res = await fetch(`${API}/api/predict`, {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        team_a: $("teamA").value, team_b: $("teamB").value, referee: $("referee").value,
        neutral: $("neutral").checked, knockout: $("knockout").checked,
        use_form: $("useForm").checked, n_sims: Number($("sims").value),
      }),
    });
    if (!res.ok) throw new Error((await res.json()).detail || "Error");
    render(await res.json());
  } catch (e) { flashError(e.message); }
  finally {
    btn.classList.remove("loading");
    btn.querySelector(".btn-text").textContent = "Ejecutar predicción";
  }
}

function flashError(msg) {
  $("results").innerHTML = `<div class="empty-state"><i data-lucide="alert-triangle" class="empty-icon"></i><h3>${msg}</h3></div>`;
  icons();
}

function stakeClass(s) {
  if (!s) return "";
  if (s.startsWith("Necesita ganar") || s.startsWith("Gana para")) return "st-win";
  if (s.startsWith("Le vale el empate") || s.startsWith("Empate para")) return "st-draw";
  if (s === "Eliminado") return "st-out";
  if (s === "Clasificado" || s === "1º asegurado" || s.startsWith("Clasificado")) return "st-ok";
  return "st-dep";
}
const stakeBadge = (s) => s ? `<span class="stake ${stakeClass(s)}">${s}</span>` : "";
const formChip = (d) => d ? `<span class="form-chip ${d > 0 ? "up" : "dn"}">forma ${d > 0 ? "+" : ""}${d}</span>` : "";

function render(d) {
  const a = d.teams.a, b = d.teams.b, o = d.outcome, g = d.goals, c = d.corners, k = d.cards;
  const favored = o.a_win >= o.b_win ? a : b;
  const knockoutCard = d.knockout
    ? `<div class="card span6">
        <div class="card-head"><h3>Pase de ronda (eliminatoria)</h3><span class="card-tag">incl. prórroga/penaltis</span></div>
        ${miniBar(a.name, d.knockout.advance_a)}${miniBar(b.name, d.knockout.advance_b)}
        <div class="stat-row"><span class="stat-label">Llega a prórroga</span><span class="stat-val">${pct(d.knockout.to_extra_time)}</span></div>
      </div>` : "";

  $("results").innerHTML = `
    <div class="cards-grid">
      <div class="card matchup">
        <div class="matchup-teams">
          <div class="mt-side"><span class="mt-flag ${fi(a.iso)}"></span><span class="mt-name">${a.name}</span><span class="mt-elo">Elo ${a.elo}</span>${formChip(a.form_delta)}${stakeBadge(a.stake)}</div>
          <div class="mt-vs">VS<br/><span style="font-size:11px">${d.referee.name}</span></div>
          <div class="mt-side"><span class="mt-flag ${fi(b.iso)}"></span><span class="mt-name">${b.name}</span><span class="mt-elo">Elo ${b.elo}</span>${formChip(b.form_delta)}${stakeBadge(b.stake)}</div>
        </div>
        <div class="prob-bar">
          <div class="prob-seg seg-a" style="width:${o.a_win * 100}%">${o.a_win > 0.07 ? pct(o.a_win) : ""}</div>
          <div class="prob-seg seg-d" style="width:${o.draw * 100}%">${o.draw > 0.07 ? pct(o.draw) : ""}</div>
          <div class="prob-seg seg-b" style="width:${o.b_win * 100}%">${o.b_win > 0.07 ? pct(o.b_win) : ""}</div>
        </div>
        <div class="prob-legend"><span><strong>${a.name}</strong> gana</span><span><strong>Empate</strong></span><span><strong>${b.name}</strong> gana</span></div>
      </div>

      <div class="card span6">
        <div class="card-head"><h3>Goles esperados (xG)</h3><span class="card-tag">Poisson</span></div>
        <div class="metrics"><div class="metric accent"><div class="big">${g.xg_a}</div><div class="lbl">${a.name}</div></div><div class="metric blue"><div class="big">${g.xg_b}</div><div class="lbl">${b.name}</div></div></div>
        <div class="stat-row"><span class="stat-label">Ambos marcan (BTTS)</span><span class="stat-val">${pct(g.btts)}</span></div>
        <div class="stat-row"><span class="stat-label">Más de 1.5 goles</span><span class="stat-val">${pct(g.over_15)}</span></div>
        <div class="stat-row"><span class="stat-label">Más de 2.5 goles</span><span class="stat-val">${pct(g.over_25)}</span></div>
        <div class="stat-row"><span class="stat-label">Más de 3.5 goles</span><span class="stat-val">${pct(g.over_35)}</span></div>
      </div>

      <div class="card span6">
        <div class="card-head"><h3>Marcadores más probables</h3><span class="card-tag">${d.config.n_sims.toLocaleString("es-ES")} sims</span></div>
        <div class="scores">${g.top_scores.map((s) => scoreRow(s, g.top_scores[0].prob)).join("")}</div>
      </div>

      <div class="card span6">
        <div class="card-head"><h3>Córners</h3><span class="card-tag">media ${c.avg_total}</span></div>
        <div class="metrics"><div class="metric"><div class="big">${c.avg_a}</div><div class="lbl">${a.name}</div></div><div class="metric"><div class="big">${c.avg_b}</div><div class="lbl">${b.name}</div></div></div>
        <div class="stat-row"><span class="stat-label">Más de 9.5 córners</span><span class="stat-val">${pct(c.over_95)}</span></div>
        <div class="stat-row"><span class="stat-label">Más de 10.5 córners</span><span class="stat-val">${pct(c.over_105)}</span></div>
      </div>

      <div class="card span6 ref-card">
        <div class="card-head"><h3>Impacto del árbitro</h3><span class="card-tag">tarjetas & penaltis</span></div>
        <span class="ref-style-tag">${d.referee.style}</span>
        <div class="ref-name">${d.referee.name}</div>
        <div class="ref-sub">${d.referee.country}${d.referee.matches ? ` · ${d.referee.matches} partidos` : ""} · histórico ${d.referee.yellows} amar.${d.referee.fouls ? ` · ${d.referee.fouls} faltas/p` : ""} · tensión ${k.tension}</div>
        <div class="metrics"><div class="metric warn"><div class="big">${k.yellows_total}</div><div class="lbl"><span class="card-sq y"></span> amarillas totales</div></div><div class="metric danger"><div class="big">${pct(k.red_prob)}</div><div class="lbl"><span class="card-sq r"></span> prob. de roja</div></div></div>
        <div class="stat-row"><span class="stat-label">Amarillas ${a.name}</span><span class="stat-val">${k.yellows_a}</span></div>
        <div class="stat-row"><span class="stat-label">Amarillas ${b.name}</span><span class="stat-val">${k.yellows_b}</span></div>
        <div class="stat-row"><span class="stat-label">Más de 4.5 tarjetas</span><span class="stat-val">${pct(k.over_45)}</span></div>
        <div class="stat-row"><span class="stat-label">Probabilidad de penalti</span><span class="stat-val">${pct(k.pen_prob)}</span></div>
      </div>

      ${knockoutCard}

      <div class="card ${d.knockout ? "span6" : "span12"}">
        <div class="card-head"><h3>Veredicto del modelo</h3><span class="card-tag">resumen</span></div>
        <p style="font-size:14.5px;line-height:1.7;color:var(--text)">
          El modelo favorece a <strong style="color:var(--accent)">${favored.name}</strong>
          (${pct(Math.max(o.a_win, o.b_win))} de victoria), marcador más probable <strong>${g.top_scores[0].score}</strong>
          y <strong>${(g.xg_a + g.xg_b).toFixed(1)} goles</strong> esperados.
          Con ${d.referee.name} se proyectan <strong>${k.yellows_total} tarjetas</strong> y un ${pct(k.pen_prob)} de penalti.
          ${(a.form_delta || b.form_delta) ? `Pondera la forma real en el Mundial (${a.name} ${a.form_delta >= 0 ? "+" : ""}${a.form_delta}, ${b.name} ${b.form_delta >= 0 ? "+" : ""}${b.form_delta} Elo).` : ""}
          ${(a.stake || b.stake) ? `Intereses: ${a.name} «${a.stake || "—"}», ${b.name} «${b.stake || "—"}».` : ""}
        </p>
      </div>
    </div>`;
  icons();
}

const scoreRow = (s, max) => `<div class="score-row"><span class="score-val">${s.score}</span><div class="score-bar"><div class="score-fill" style="width:${(s.prob / max) * 100}%"></div></div><span class="score-pct">${pct(s.prob)}</span></div>`;
const miniBar = (name, p) => `<div class="mini"><div class="mini-row"><span>${name}</span><strong>${pct(p)}</strong></div><div class="mini-track"><div class="mini-fill" style="width:${p * 100}%"></div></div></div>`;

/* ---------- Grupos ---------- */
async function loadGroups() {
  const groups = await fetch(`${API}/api/groups`).then((r) => r.json());
  $("groupsGrid").innerHTML = Object.entries(groups).map(([letter, rows]) => {
    const body = rows.map((r, i) => {
      const cls = i === 0 ? "q1" : i === 1 ? "q2" : "";
      const fc = r.form > 0 ? "form-up" : r.form < 0 ? "form-dn" : "form-zero";
      const fv = r.form > 0 ? `+${r.form}` : `${r.form}`;
      return `<tr class="${cls}">
        <td class="pos">${i + 1}</td>
        <td class="team"><span class="gflag flag-cell ${fi(r.iso)}"></span>${r.name}</td>
        <td>${r.pld ?? "-"}</td><td>${r.w ?? "-"}</td><td>${r.d ?? "-"}</td><td>${r.l ?? "-"}</td>
        <td>${r.gd > 0 ? "+" + r.gd : (r.gd ?? "-")}</td>
        <td class="pts">${r.pts ?? "-"}</td>
        <td class="${fc}">${fv}</td>
      </tr>`;
    }).join("");
    return `<div class="group-card"><h3>Grupo ${letter}</h3>
      <table class="gtable">
        <thead><tr><th>#</th><th class="left">Equipo</th><th>PJ</th><th>G</th><th>E</th><th>P</th><th>DG</th><th>Pts</th><th>Forma</th></tr></thead>
        <tbody>${body}</tbody>
      </table></div>`;
  }).join("");
}

/* ---------- Calendario ---------- */
let SCHEDULE = [];
async function loadSchedule() {
  const data = await fetch(`${API}/api/schedule`).then((r) => r.json());
  SCHEDULE = data.fixtures;
  $("roundsStrip").innerHTML = data.rounds.map(
    (r) => `<div class="round-pill"><strong>${r.round}</strong> · <span>${r.dates}</span></div>`
  ).join("");

  const now = Date.now();
  const fmt = (utc) => new Date(utc).toLocaleString("es-ES", {
    weekday: "short", day: "numeric", month: "short", hour: "2-digit", minute: "2-digit",
  });
  const side = (s, right) => {
    const flag = s.code ? `<span class="fxflag ${fi(s.iso)}"></span>` : "";
    const name = s.code ? `<span>${s.name}${stakeBadge(s.stake)}</span>` : `<span>${s.label}</span>`;
    const inner = right ? `${name}${flag}` : `${flag}${name}`;
    return `<div class="fx-side ${right ? "right" : ""} ${s.code ? "" : "tbd"}">${inner}</div>`;
  };

  $("fixtures").innerHTML = SCHEDULE.map((f, i) => {
    const t = new Date(f.utc).getTime();
    const started = t < now;
    const live = started && (now - t) < 2 * 3600 * 1000;
    const statusTxt = live ? " · en juego" : (started ? " · jugado" : "");
    return `
      <div class="fixture ${started ? "past" : ""}">
        <div class="fx-meta"><span class="fx-num">${f.phase}</span><span>${fmt(f.utc)}<span class="played">${statusTxt}</span></span></div>
        <div class="fx-teams">${side(f.a, false)}<span class="fx-vs">VS</span>${side(f.b, true)}</div>
        <div class="fx-venue"><i data-lucide="map-pin"></i> ${f.venue}</div>
        ${f.referee ? `<div class="fx-ref"><i data-lucide="user-round"></i> ${f.referee.name} <span>(${f.referee.country} · ${f.referee.style}${f.referee.estimated ? " · est." : ""})</span></div>` : `<div class="fx-ref tbd-ref"><i data-lucide="user-round"></i> <span>árbitro por designar</span></div>`}
        <button class="fx-predict" ${f.playable ? `data-i="${i}"` : "disabled"}>
          ${f.playable ? '<i data-lucide="sparkles"></i> Predecir este partido' : "Rival por determinar"}
        </button>
      </div>`;
  }).join("");

  $("fixtures").querySelectorAll(".fx-predict[data-i]").forEach((btn) =>
    btn.addEventListener("click", () => {
      const f = SCHEDULE[Number(btn.dataset.i)];
      $("teamA").value = f.a.code;
      $("teamB").value = f.b.code;
      if (f.referee) $("referee").value = f.referee.id;
      $("knockout").checked = f.phase.startsWith("Ronda");
      $("neutral").checked = true;
      updateFlags(); updateRefMeta(); switchTab("predictor"); run();
      window.scrollTo({ top: 0, behavior: "smooth" });
    }));
  icons();
}

boot();
