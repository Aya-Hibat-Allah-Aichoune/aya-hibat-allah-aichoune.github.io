/*
 * HogarHub — API client
 * Same REST contract as the real backend (backend/main.py · FastAPI + SQLite):
 *   GET    /api/properties?city=&type=&max_price=&q=
 *   POST   /api/properties            (requires token)
 *   DELETE /api/properties/{id}       (requires token)
 *   POST   /api/auth/login            -> { token, user }
 *   POST   /api/contact               -> visit request
 *   GET    /api/stats
 * If the backend is not running (GitHub Pages demo), a local engine with the
 * same interface answers from localStorage, so the demo is fully functional.
 */
(function () {
  const BACKEND = "http://localhost:8000";
  const DB_KEY = "hogarhub_db_v1", FAV_KEY = "hogarhub_favs_v1", TOKEN_KEY = "hogarhub_token";
  let backendAlive = null;
  const delay = (ms) => new Promise(r => setTimeout(r, ms));

  function db() {
    let d = JSON.parse(localStorage.getItem(DB_KEY) || "null");
    if (!d) { d = { properties: [...window.HOGAR_SEED], visits: [] }; localStorage.setItem(DB_KEY, JSON.stringify(d)); }
    return d;
  }
  function save(d) { localStorage.setItem(DB_KEY, JSON.stringify(d)); }

  async function tryBackend(path, opts) {
    if (backendAlive === false) return null;
    try {
      const ctrl = new AbortController(); const t = setTimeout(() => ctrl.abort(), 900);
      const res = await fetch(BACKEND + path, { ...opts, signal: ctrl.signal, headers: { "Content-Type": "application/json", ...(opts && opts.headers) } });
      clearTimeout(t); backendAlive = true;
      if (!res.ok) throw new Error(res.status);
      return await res.json();
    } catch { backendAlive = false; return null; }
  }

  const Local = {
    async list(f = {}) {
      await delay(220);
      return db().properties.filter(p =>
        (!f.q || (p.title + p.city + p.zone).toLowerCase().includes(f.q.toLowerCase())) &&
        (!f.city || p.city === f.city) && (!f.type || p.type === f.type) &&
        (!f.rooms || p.rooms >= +f.rooms) && (!f.max || p.price <= +f.max));
    },
    async create(data, token) {
      await delay(300); if (!token) throw new Error("401 · Inicia sesión para publicar");
      const d = db(); const item = { id: Date.now(), badge: "Nuevo", features: ["Publicado por ti"], ...data };
      d.properties.unshift(item); save(d); return item;
    },
    async remove(id, token) {
      await delay(200); if (!token) throw new Error("401 · Inicia sesión");
      const d = db(); d.properties = d.properties.filter(p => p.id !== id); save(d); return { ok: true };
    },
    async login(email) { await delay(350); return { token: "demo-token-" + btoa(email).slice(0, 10), user: { name: "Aya (demo)", email } }; },
    async contact(data) { await delay(300); const d = db(); d.visits.push({ ...data, at: new Date().toISOString() }); save(d); return { ok: true, message: "Visita solicitada. El agente te contactará hoy." }; },
    async stats() {
      await delay(200); const ps = db().properties;
      const byCity = {}; ps.forEach(p => byCity[p.city] = (byCity[p.city] || 0) + 1);
      return { total: ps.length, cities: Object.keys(byCity).length, byCity,
        avgPrice: Math.round(ps.reduce((a, p) => a + p.price, 0) / (ps.length || 1)),
        visits: db().visits.length, favs: JSON.parse(localStorage.getItem(FAV_KEY) || "[]").length };
    }
  };

  window.HogarAPI = {
    mode: () => backendAlive ? "Backend FastAPI conectado" : "Modo demo local (misma API REST)",
    token: () => localStorage.getItem(TOKEN_KEY),
    setToken: (t) => t ? localStorage.setItem(TOKEN_KEY, t) : localStorage.removeItem(TOKEN_KEY),
    favs: () => new Set(JSON.parse(localStorage.getItem(FAV_KEY) || "[]")),
    toggleFav(id) { const f = this.favs(); f.has(id) ? f.delete(id) : f.add(id); localStorage.setItem(FAV_KEY, JSON.stringify([...f])); return f; },
    async list(f) { return (await tryBackend("/api/properties?" + new URLSearchParams(f))) ?? Local.list(f); },
    async create(data) { return (await tryBackend("/api/properties", { method: "POST", body: JSON.stringify(data), headers: { Authorization: "Bearer " + this.token() } })) ?? Local.create(data, this.token()); },
    async remove(id) { return (await tryBackend("/api/properties/" + id, { method: "DELETE", headers: { Authorization: "Bearer " + this.token() } })) ?? Local.remove(id, this.token()); },
    async login(email, pass) { return (await tryBackend("/api/auth/login", { method: "POST", body: JSON.stringify({ email, password: pass }) })) ?? Local.login(email); },
    async contact(data) { return (await tryBackend("/api/contact", { method: "POST", body: JSON.stringify(data) })) ?? Local.contact(data); },
    async stats() { return (await tryBackend("/api/stats")) ?? Local.stats(); }
  };
})();
