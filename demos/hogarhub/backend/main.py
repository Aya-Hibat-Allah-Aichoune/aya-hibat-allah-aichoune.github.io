"""
HogarHub — Backend API (FastAPI + SQLite)
Plataforma inmobiliaria · Proyecto de Aya Hibat Allah Aichoune

Run:
    pip install -r requirements.txt
    uvicorn main:app --reload --port 8000
Docs (Swagger): http://localhost:8000/docs

Endpoints:
    GET    /api/properties?city=&type=&rooms=&max_price=&q=
    GET    /api/properties/{id}
    POST   /api/properties          (Authorization: Bearer <token>)
    DELETE /api/properties/{id}     (Authorization: Bearer <token>)
    POST   /api/auth/login          -> {token, user}
    POST   /api/contact             -> visit request
    GET    /api/stats
Auth is a signed demo token (HMAC). In production this maps 1:1 to JWT
(the frontend contract does not change).
"""
import hashlib, hmac, json, sqlite3, time
from pathlib import Path
from typing import Optional

from fastapi import Depends, FastAPI, Header, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

DB = Path(__file__).with_name("hogarhub.db")
SECRET = b"hogarhub-demo-secret-change-in-production"

app = FastAPI(title="HogarHub API", version="1.0.0", description="Real-estate platform API")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

SEED = [
    (1, "Ático luminoso con terraza en el Ensanche", "Santiago de Compostela", "Ensanche", 285000, "Ático", 3, 2, 98, "https://images.unsplash.com/photo-1502672260266-1c1ef2d93688?q=80&w=1200&auto=format&fit=crop", "Destacado", "Lucía Fernández", "Ático reformado con terraza de 18 m² y vistas despejadas.", json.dumps(["Terraza 18 m²", "Garaje", "Suelo radiante"])),
    (2, "Piso familiar junto al Parque de la Alameda", "Santiago de Compostela", "Alameda", 219000, "Piso", 3, 1, 84, "https://images.unsplash.com/photo-1522708323590-d24dbb6b0267?q=80&w=1200&auto=format&fit=crop", "Nuevo", "Lucía Fernández", "Piso exterior a 5 minutos de la Catedral.", json.dumps(["Exterior", "Balcón", "Ascensor"])),
    (3, "Casa con jardín y piscina en Ames", "A Coruña", "Ames", 390000, "Casa", 4, 3, 176, "https://images.unsplash.com/photo-1600596542815-ffad4c1539a9?q=80&w=1200&auto=format&fit=crop", "Destacado", "Marcos Vidal", "Chalet independiente con jardín de 400 m² y piscina.", json.dumps(["Piscina", "Jardín 400 m²", "Garaje doble"])),
    (4, "Estudio moderno para inversores en el centro", "Vigo", "Centro", 118000, "Estudio", 1, 1, 38, "https://images.unsplash.com/photo-1493809842364-78817add7ffb?q=80&w=1200&auto=format&fit=crop", "Oportunidad", "Ana Prado", "Estudio amueblado, rentabilidad estimada del 6,1%.", json.dumps(["Amueblado", "Rentabilidad 6,1%"])),
    (5, "Piso de diseño en Malasaña", "Madrid", "Malasaña", 465000, "Piso", 2, 2, 92, "https://images.unsplash.com/photo-1560448204-e02f11c3d0e2?q=80&w=1200&auto=format&fit=crop", "Nuevo", "Carmen Ruiz", "Reforma de autor en el corazón de Malasaña.", json.dumps(["Reforma de autor", "2 suites"])),
]


def conn():
    c = sqlite3.connect(DB); c.row_factory = sqlite3.Row; return c


def init_db():
    with conn() as c:
        c.execute("""CREATE TABLE IF NOT EXISTS properties(
            id INTEGER PRIMARY KEY, title TEXT, city TEXT, zone TEXT, price INTEGER,
            type TEXT, rooms INTEGER, baths INTEGER, m2 INTEGER, img TEXT,
            badge TEXT, agent TEXT, desc TEXT, features TEXT)""")
        c.execute("CREATE TABLE IF NOT EXISTS visits(id INTEGER PRIMARY KEY AUTOINCREMENT, property INTEGER, name TEXT, email TEXT, date TEXT, created_at TEXT)")
        if c.execute("SELECT COUNT(*) FROM properties").fetchone()[0] == 0:
            c.executemany("INSERT INTO properties VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)", SEED)


@app.on_event("startup")
def startup(): init_db()


def row(p): d = dict(p); d["features"] = json.loads(d["features"] or "[]"); return d


# ---------- auth (demo HMAC token, JWT-compatible contract) ----------
def make_token(email: str) -> str:
    payload = f"{email}.{int(time.time()) + 86400}"
    sig = hmac.new(SECRET, payload.encode(), hashlib.sha256).hexdigest()[:24]
    return f"{payload}.{sig}"


def require_auth(authorization: Optional[str] = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "Missing Bearer token")
    token = authorization[7:]
    try:
        email, exp, sig = token.rsplit(".", 2)
        expected = hmac.new(SECRET, f"{email}.{exp}".encode(), hashlib.sha256).hexdigest()[:24]
        if not hmac.compare_digest(sig, expected) or int(exp) < time.time():
            raise ValueError
    except Exception:
        raise HTTPException(401, "Invalid or expired token")
    return email


class LoginIn(BaseModel): email: str; password: str = Field(min_length=4)
class PropertyIn(BaseModel):
    title: str; city: str; zone: str; price: int = Field(gt=0); type: str
    rooms: int = Field(ge=1, le=20); baths: int = Field(ge=1, le=10); m2: int = Field(gt=0)
    img: str = ""; badge: str = "Nuevo"; agent: str = "Demo"; desc: str = ""; features: list[str] = []
class ContactIn(BaseModel): property: int; name: str; email: str; date: str


@app.post("/api/auth/login", tags=["auth"])
def login(body: LoginIn):
    return {"token": make_token(body.email), "user": {"name": body.email.split("@")[0].title(), "email": body.email}}


@app.get("/api/properties", tags=["properties"])
def list_properties(q: str = "", city: str = "", type: str = "", rooms: int = 0, max_price: int = Query(0, alias="max")):
    with conn() as c: rows = [row(r) for r in c.execute("SELECT * FROM properties ORDER BY id DESC")]
    return [p for p in rows if (not q or q.lower() in (p["title"] + p["city"] + p["zone"]).lower())
            and (not city or p["city"] == city) and (not type or p["type"] == type)
            and (not rooms or p["rooms"] >= rooms) and (not max_price or p["price"] <= max_price)]


@app.get("/api/properties/{pid}", tags=["properties"])
def get_property(pid: int):
    with conn() as c: r = c.execute("SELECT * FROM properties WHERE id=?", (pid,)).fetchone()
    if not r: raise HTTPException(404, "Property not found")
    return row(r)


@app.post("/api/properties", status_code=201, tags=["properties"])
def create_property(body: PropertyIn, _user: str = Depends(require_auth)):
    with conn() as c:
        cur = c.execute("INSERT INTO properties(title,city,zone,price,type,rooms,baths,m2,img,badge,agent,desc,features) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
                        (body.title, body.city, body.zone, body.price, body.type, body.rooms, body.baths, body.m2, body.img, body.badge, body.agent, body.desc, json.dumps(body.features)))
        r = c.execute("SELECT * FROM properties WHERE id=?", (cur.lastrowid,)).fetchone()
    return row(r)


@app.delete("/api/properties/{pid}", tags=["properties"])
def delete_property(pid: int, _user: str = Depends(require_auth)):
    with conn() as c:
        if c.execute("DELETE FROM properties WHERE id=?", (pid,)).rowcount == 0:
            raise HTTPException(404, "Property not found")
    return {"ok": True}


@app.post("/api/contact", status_code=201, tags=["contact"])
def contact(body: ContactIn):
    with conn() as c:
        if not c.execute("SELECT 1 FROM properties WHERE id=?", (body.property,)).fetchone():
            raise HTTPException(404, "Property not found")
        c.execute("INSERT INTO visits(property,name,email,date,created_at) VALUES (?,?,?,?,datetime('now'))",
                  (body.property, body.name, body.email, body.date))
    return {"ok": True, "message": "Visita solicitada. El agente te contactará hoy."}


@app.get("/api/stats", tags=["stats"])
def stats():
    with conn() as c:
        ps = [row(r) for r in c.execute("SELECT * FROM properties")]
        visits = c.execute("SELECT COUNT(*) FROM visits").fetchone()[0]
    by_city = {}
    for p in ps: by_city[p["city"]] = by_city.get(p["city"], 0) + 1
    return {"total": len(ps), "cities": len(by_city), "byCity": by_city,
            "avgPrice": round(sum(p["price"] for p in ps) / len(ps)) if ps else 0, "visits": visits}
