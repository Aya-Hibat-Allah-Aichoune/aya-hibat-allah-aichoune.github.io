/* HogarHub — UI logic (consumes HogarAPI, same contract as FastAPI backend) */
const $ = (id) => document.getElementById(id);
const fmt = (n) => new Intl.NumberFormat("es-ES").format(n) + " €";
let filters = { q: "", city: "", type: "", rooms: "", max: "", sort: "" };
let onlyFavs = false, current = null, allCache = [];

function toast(msg) { const t = $("toast"); t.textContent = msg; t.classList.add("show"); setTimeout(() => t.classList.remove("show"), 2800); }
function specs(p) { return `<span>🛏️ ${p.rooms} hab.</span><span>🛁 ${p.baths} baños</span><span>📐 ${p.m2} m²</span>`; }

async function load() {
  let list = await HogarAPI.list(filters);
  if (filters.sort === "low") list.sort((a, b) => a.price - b.price);
  if (filters.sort === "high") list.sort((a, b) => b.price - a.price);
  if (filters.sort === "m2") list.sort((a, b) => b.m2 - a.m2);
  if (filters.sort === "rooms") list.sort((a, b) => b.rooms - a.rooms);
  if (onlyFavs) list = list.filter(p => HogarAPI.favs().has(p.id));
  renderGrid(list); renderHeaderStats();
}
function renderGrid(list) {
  const favs = HogarAPI.favs();
  $("favCount").textContent = favs.size;
  $("resultCount").textContent = `${list.length} vivienda${list.length !== 1 ? "s" : ""} ${onlyFavs ? "en tus favoritos" : "disponibles"}`;
  $("empty").classList.toggle("hidden", list.length > 0);
  $("grid").innerHTML = list.map(p => `
    <article class="card" onclick="openDetail(${p.id})">
      <div class="photo"><img src="${p.img}" alt="${p.title}" loading="lazy" onerror="this.src='https://images.unsplash.com/photo-1560448204-e02f11c3d0e2?q=80&w=1200&auto=format&fit=crop'">
        ${p.badge ? `<span class="badge">${p.badge}</span>` : ""}
        <button class="fav" title="Guardar en favoritos" onclick="event.stopPropagation();toggleFav(${p.id})">${favs.has(p.id) ? "❤️" : "🤍"}</button>
      </div>
      <div class="body">
        <div class="price-row"><span class="price">${fmt(p.price)}</span><span class="perm2">${fmt(Math.round(p.price / p.m2))}/m²</span></div>
        <h3>${p.title}</h3><p class="place">📍 ${p.zone} · ${p.city}</p>
        <div class="specs">${specs(p)}</div>
      </div>
    </article>`).join("");
}
async function renderHeaderStats() {
  const s = await HogarAPI.stats();
  $("stTotal").textContent = s.total; $("stCities").textContent = s.cities;
  $("stAvg").textContent = fmt(s.avgPrice); $("stVisits").textContent = s.visits;
  $("apiMode").textContent = HogarAPI.mode();
  return s;
}
async function toggleFav(id) { HogarAPI.toggleFav(id); toast(HogarAPI.favs().has(id) ? "❤️ Guardado en favoritos" : "Eliminado de favoritos"); load(); window["toggleFav"] = toggleFav; }
window.toggleFav = toggleFav;

function openDetail(id) {
  const p = allCache.find(x => x.id === id); if (!p) return; current = p;
  $("dImg").src = p.img; $("dTitle").textContent = p.title;
  $("dPlace").textContent = `📍 ${p.zone} · ${p.city} · Agente: ${p.agent}`;
  $("dAgent").textContent = p.agent;
  $("dBadge").textContent = p.badge || p.type; $("dBadge").style.display = "inline-block";
  $("dPrice").textContent = fmt(p.price); $("dM2").textContent = fmt(Math.round(p.price / p.m2)) + "/m²";
  $("dSpecs").innerHTML = specs(p) + `<span>🏷️ ${p.type}</span>`;
  $("dDesc").textContent = p.desc; $("dFeatures").innerHTML = p.features.map(f => `<span>✓ ${f}</span>`).join("");
  $("visitMsg").textContent = ""; calcMortgage(); $("detailDialog").showModal();
}
window.openDetail = openDetail;

async function refreshCache() { allCache = await HogarAPI.list({}); 
  const cities = [...new Set(allCache.map(p => p.city))];
  $("cityChips").innerHTML = `<button class="chip ${!filters.city ? "on" : ""}" data-city="">Todas</button>` +
    cities.map(c => `<button class="chip ${filters.city === c ? "on" : ""}" data-city="${c}">${c}</button>`).join("");
  $("cityChips").querySelectorAll(".chip").forEach(ch => ch.onclick = () => { filters.city = ch.dataset.city; refreshCache(); load(); });
  $("cities").innerHTML = cities.map(c => `<option value="${c}">`).join("");
}

function calcMortgage() {
  if (!current) return;
  const down = +$("mDown").value || 0, years = +$("mYears").value || 30, rate = (+$("mRate").value || 0) / 100 / 12;
  const principal = current.price * (1 - down / 100), n = years * 12;
  const m = rate ? principal * rate * Math.pow(1 + rate, n) / (Math.pow(1 + rate, n) - 1) : principal / n;
  $("mResult").textContent = fmt(Math.round(m)) + "/mes";
}
["mDown", "mYears", "mRate"].forEach(id => $(id).addEventListener("input", calcMortgage));

$("searchForm").addEventListener("submit", e => { e.preventDefault(); filters.q = $("q").value; filters.type = $("qType").value; filters.max = $("qMax").value; switchView("explore"); load(); });
$("fRooms").addEventListener("change", e => { filters.rooms = e.target.value; load(); });
$("sort").addEventListener("change", e => { filters.sort = e.target.value; load(); });
function resetFilters() { filters = { q: "", city: "", type: "", rooms: "", max: "", sort: "" }; onlyFavs = false; ["q"].forEach(i => $(i).value = ""); ["qType","qMax","fRooms","sort"].forEach(i => $(i).value = ""); refreshCache(); load(); }
window.resetFilters = resetFilters;

/* Views */
function switchView(v) {
  onlyFavs = v === "favs";
  const target = v === "favs" ? "explore" : v;
  document.querySelectorAll(".navlink").forEach(b => b.classList.toggle("active", b.dataset.view === v));
  ["explore", "dashboard", "publish"].forEach(name => $("view-" + name).classList.toggle("hidden", name !== target));
  if (v === "dashboard") renderDashboard();
  if (target === "explore") load();
  window.scrollTo({ top: document.querySelector("main").offsetTop - 70, behavior: "smooth" });
}
document.querySelectorAll(".navlink").forEach(b => b.addEventListener("click", () => switchView(b.dataset.view)));

/* Dashboard */
async function renderDashboard() {
  const s = await renderHeaderStats(); const ps = allCache.length ? allCache : await HogarAPI.list({});
  $("kTotal").textContent = s.total; $("kAvg").textContent = fmt(s.avgPrice); $("kVisits").textContent = s.visits;
  $("kM2").textContent = fmt(Math.round(ps.reduce((a, p) => a + p.price / p.m2, 0) / (ps.length || 1)));
  drawBars($("chartCity"), Object.entries(s.byCity).sort((a, b) => b[1] - a[1]), "#6d28d9", v => v);
  const byType = {}; ps.forEach(p => byType[p.type] = (byType[p.type] || 0) + 1);
  drawBars($("chartType"), Object.entries(byType), "#db2777", v => v);
  const logged = !!HogarAPI.token();
  $("tableBody").innerHTML = ps.map(p => `<tr><td>${p.title.slice(0, 42)}…</td><td>${p.city}</td><td>${p.type}</td><td>${p.rooms}</td><td>${p.m2}</td><td>${fmt(p.price)}</td><td>${fmt(Math.round(p.price / p.m2))}</td>
    <td>${logged ? `<button class="del" onclick="removeProp(${p.id})">Eliminar</button>` : `<span class="muted small">🔒 login</span>`}</td></tr>`).join("");
}
function drawBars(cv, entries, color, fmtV) {
  const ctx = cv.getContext("2d"), W = cv.width, H = cv.height, max = Math.max(...entries.map(e => e[1]), 1);
  ctx.clearRect(0, 0, W, H); const bw = Math.min(64, (W - 40) / entries.length - 18);
  entries.forEach(([label, v], i) => {
    const x = 30 + i * ((W - 40) / entries.length), h = (H - 70) * (v / max), y = H - 42 - h;
    ctx.fillStyle = color; ctx.beginPath(); ctx.roundRect(x, y, bw, h, 7); ctx.fill();
    ctx.fillStyle = "#0f172a"; ctx.font = "800 14px Inter"; ctx.textAlign = "center"; ctx.fillText(fmtV(v), x + bw / 2, y - 7);
    ctx.fillStyle = "#64748b"; ctx.font = "600 11px Inter";
    const words = label.split(" "); ctx.fillText(words[0], x + bw / 2, H - 24); if (words[1]) ctx.fillText(words.slice(1).join(" "), x + bw / 2, H - 10);
  });
}
async function removeProp(id) { try { await HogarAPI.remove(id); toast("🗑️ Vivienda eliminada"); await refreshCache(); renderDashboard(); } catch (e) { toast(e.message); } }
window.removeProp = removeProp;

/* Publish & auth & visit */
function updateAuthUI() {
  const t = HogarAPI.token();
  $("userChip").classList.toggle("hidden", !t); $("userChip").textContent = t ? "🔐 Sesión demo activa" : "";
  $("authBtn").textContent = t ? "Cerrar sesión" : "Iniciar sesión";
}
$("authBtn").addEventListener("click", () => { if (HogarAPI.token()) { HogarAPI.setToken(null); updateAuthUI(); toast("Sesión cerrada"); } else { $("authMsg").textContent = ""; $("authDialog").showModal(); } });
$("authForm").addEventListener("submit", async e => {
  e.preventDefault();
  try { const r = await HogarAPI.login($("aEmail").value, $("aPass").value); HogarAPI.setToken(r.token); updateAuthUI(); $("authDialog").close(); toast(`✅ Bienvenida, ${r.user.name}. Token guardado.`); if (!$("view-publish").classList.contains("hidden")) $("publishMsg").textContent = "Sesión activa: ya puedes publicar."; }
  catch (err) { $("authMsg").textContent = err.message; $("authMsg").classList.add("err"); }
});
$("publishForm").addEventListener("submit", async e => {
  e.preventDefault(); const msg = $("publishMsg"); msg.classList.remove("err");
  if (!HogarAPI.token()) { msg.textContent = "🔒 Primero inicia sesión (botón arriba). Es gratis y es demo."; msg.classList.add("err"); $("authDialog").showModal(); return; }
  try {
    const item = await HogarAPI.create({
      title: $("pTitle").value, city: $("pCity").value, zone: $("pZone").value, price: +$("pPrice").value,
      type: $("pType").value, rooms: +$("pRooms").value, baths: +$("pBaths").value, m2: +$("pM2").value,
      img: $("pImg").value || "https://images.unsplash.com/photo-1560448204-e02f11c3d0e2?q=80&w=1200&auto=format&fit=crop",
      desc: $("pDesc").value || "Vivienda publicada desde el panel de HogarHub.", agent: "Tú (demo)"
    });
    msg.textContent = `🎉 Publicada: «${item.title}». Ya está en Explorar.`; e.target.reset();
    await refreshCache(); toast("🚀 Vivienda publicada");
  } catch (err) { msg.textContent = err.message; msg.classList.add("err"); }
});
$("visitForm").addEventListener("submit", async e => {
  e.preventDefault(); if (!$("vDate").value) return;
  const r = await HogarAPI.contact({ property: current.id, name: $("vName").value, email: $("vEmail").value, date: $("vDate").value });
  $("visitMsg").textContent = "✅ " + r.message; toast("📅 Visita solicitada"); renderHeaderStats();
});

/* Init */
(async function init() { await refreshCache(); updateAuthUI(); await load(); })();
