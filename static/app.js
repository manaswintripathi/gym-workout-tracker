// Built by Manaswin Tripathi (@manaswintripathi)
const $ = (id) => document.getElementById(id);
const api = async (path, opts) => {
  const r = await fetch(path, opts);
  if (!r.ok) { const e = await r.json().catch(() => ({})); throw new Error(e.error || r.statusText); }
  return r.json();
};

let editingId = null;

async function loadExercises() {
  const { exercises } = await api("/api/exercises");
  for (const sel of [$("f-exercise"), $("chart-exercise"), $("filter-exercise")]) {
    const keep = sel.value;
    sel.innerHTML = sel.id === "filter-exercise" ? '<option value="">All exercises</option>' : "";
    for (const ex of exercises) {
      const o = document.createElement("option");
      o.value = o.textContent = ex;
      sel.appendChild(o);
    }
    if (keep) sel.value = keep;
  }
  if (!$("chart-exercise").value) $("chart-exercise").value = "Bench Press";
}

async function loadSummary() {
  const s = await api("/api/summary");
  $("sum-total").textContent = s.total_workouts;
  $("sum-days").textContent = s.training_days;
  $("sum-streak").textContent = s.streak_days + " day" + (s.streak_days === 1 ? "" : "s");
  $("sum-volume").textContent = s.this_week_volume_kg.toLocaleString() + " kg";
}

async function loadOverload() {
  const ex = $("f-exercise").value;
  if (!ex) return;
  const d = await api("/api/overload/" + encodeURIComponent(ex));
  $("overload-hint").textContent = d.last_best
    ? `💪 ${ex} — best set: ${d.last_best.sets}x${d.last_best.reps} @ ${d.last_best.weight} kg (${d.last_best.date}). ${d.suggestion}`
    : `💪 ${ex} — ${d.suggestion}`;
}

function drawChart(points) {
  const c = $("chart"), ctx = c.getContext("2d");
  ctx.clearRect(0, 0, c.width, c.height);
  if (points.length < 2) { ctx.fillStyle = "#9aa3c7"; ctx.font = "16px sans-serif"; ctx.fillText("Log at least 2 sessions for this exercise to see a trend.", 20, 110); return; }
  const vals = points.map((p) => p.max_weight), min = Math.min(...vals), max = Math.max(...vals);
  const pad = 40, w = c.width - pad * 2, h = c.height - pad * 2;
  const x = (i) => pad + (i * w) / (points.length - 1);
  const y = (v) => pad + h - ((v - (min === max ? min - 5 : min)) / ((max - min) || 10)) * h;
  ctx.strokeStyle = "#2a2f4d"; ctx.beginPath(); ctx.moveTo(pad, pad); ctx.lineTo(pad, pad + h); ctx.lineTo(pad + w, pad + h); ctx.stroke();
  ctx.strokeStyle = "#ff6b35"; ctx.lineWidth = 3; ctx.beginPath();
  points.forEach((p, i) => i === 0 ? ctx.moveTo(x(i), y(p.max_weight)) : ctx.lineTo(x(i), y(p.max_weight)));
  ctx.stroke();
  ctx.fillStyle = "#eef1ff"; ctx.font = "13px sans-serif";
  points.forEach((p, i) => { ctx.beginPath(); ctx.arc(x(i), y(p.max_weight), 4, 0, 7); ctx.fill(); ctx.fillText(p.max_weight + " kg", x(i) - 18, y(p.max_weight) - 10); ctx.fillText(p.date.slice(5), x(i) - 14, c.height - 12); });
}

async function loadChart() {
  const ex = $("chart-exercise").value;
  const d = await api("/api/stats/" + encodeURIComponent(ex));
  drawChart(d.points);
  $("chart-note").textContent = d.points.length
    ? `${ex}: ${d.points.length} training days tracked. Weekly volume (all lifts): ${d.weekly_volume_kg.toLocaleString()} kg.`
    : `No data for ${ex} yet.`;
}

async function loadPRs() {
  const prs = await api("/api/prs");
  $("prs").innerHTML = prs.length ? "" : "<p>No records yet.</p>";
  for (const p of prs.slice(0, 12)) {
    const div = document.createElement("div");
    div.className = "pr";
    div.innerHTML = `<b>${p.exercise}</b><br>${p.pr_weight} kg — ${p.entry.sets}x${p.entry.reps} on ${p.entry.date}`;
    $("prs").appendChild(div);
  }
}

async function loadHistory() {
  const q = new URLSearchParams();
  if ($("filter-exercise").value) q.set("exercise", $("filter-exercise").value);
  if ($("filter-from").value) q.set("from", $("filter-from").value);
  if ($("filter-to").value) q.set("to", $("filter-to").value);
  const rows = await api("/api/workouts?" + q.toString());
  const tb = $("history");
  tb.innerHTML = rows.length ? "" : '<tr><td colspan="7">No workouts yet — log your first one above.</td></tr>';
  for (const r of rows) {
    const tr = document.createElement("tr");
    tr.innerHTML = `<td>${r.date}</td><td>${r.exercise}</td><td>${r.sets}</td><td>${r.reps}</td><td>${r.weight} kg</td><td>${r.volume.toLocaleString()} kg</td>
      <td><button class="small" data-edit="${r.id}">Edit</button> <button class="small danger" data-del="${r.id}">Delete</button></td>`;
    tb.appendChild(tr);
  }
  tb.querySelectorAll("[data-del]").forEach((b) => b.onclick = async () => {
    if (confirm("Delete this entry?")) { await api("/api/workouts/" + b.dataset.del, { method: "DELETE" }); await refresh(); }
  });
  tb.querySelectorAll("[data-edit]").forEach((b) => b.onclick = async () => {
    const weight = prompt("New weight (kg):", "");
    if (weight === null || weight === "") return;
    await api("/api/workouts/" + b.dataset.edit, { method: "PUT", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ weight: parseFloat(weight) }) });
    await refresh();
  });
}

async function refresh() {
  await Promise.all([loadSummary(), loadOverload(), loadChart(), loadPRs(), loadHistory()]);
}

$("log-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  await api("/api/workouts", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({
    date: $("f-date").value, exercise: $("f-exercise").value,
    sets: parseInt($("f-sets").value), reps: parseInt($("f-reps").value),
    weight: parseFloat($("f-weight").value), notes: $("f-notes").value }) });
  $("f-notes").value = "";
  await refresh();
});
$("f-exercise").addEventListener("change", loadOverload);
$("chart-exercise").addEventListener("change", loadChart);
$("filter-btn").addEventListener("click", loadHistory);
$("clear-btn").addEventListener("click", async () => {
  if (confirm("Delete ALL workout entries (including sample data)?")) { await api("/api/workouts/clear", { method: "POST" }); await refresh(); }
});

$("f-date").valueAsDate = new Date();
(async () => { await loadExercises(); await refresh(); })();
