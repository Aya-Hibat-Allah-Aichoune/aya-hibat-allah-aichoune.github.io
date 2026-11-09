# 🏠 HogarHub — Plataforma inmobiliaria full-stack

> Proyecto insignia de **Aya Hibat Allah Aichoune** · Desarrolladora Full Stack & Mobile
> Demo en vivo: https://aya-hibat-allah-aichoune.github.io/demos/hogarhub/

Plataforma inmobiliaria completa — buscador con filtros, favoritos, calculadora
hipotecaria, publicación de viviendas con autenticación, solicitud de visitas y
panel de estadísticas — construida **de la base de datos a la pantalla**.

Nace de mi experiencia real en **Brokerspot (Emiratos Árabes)**, donde desarrollé
una plataforma inmobiliaria en Flutter: HogarHub es esa misma idea llevada a web
con una API REST propia y una interfaz moderna.

## ✨ Funcionalidades

| Área | Qué hace |
|---|---|
| 🔍 Explorar | Búsqueda por texto, ciudad, tipo, habitaciones y precio · ordenación · tarjetas con €/m² |
| ❤️ Favoritos | Guardado persistente, contador y vista filtrada |
| 🏠 Detalle | Ficha completa, características, **calculadora de hipoteca** (cuota mensual en directo) |
| 📅 Visitas | Formulario que registra la solicitud vía API (`POST /api/contact`) |
| 🔐 Auth | Login con token (contrato tipo JWT): sin sesión no se puede publicar ni borrar |
| ➕ Publicar | CRUD real: el anuncio aparece al instante en Explorar (`POST /api/properties`) |
| 📊 Panel | KPIs, gráficas Canvas por ciudad/tipo, tabla de inventario y borrado con sesión |

## 🧱 Arquitectura

```
demos/hogarhub/
├── index.html          # SPA (Explorar · Favoritos · Panel · Publicar)
├── css/styles.css      # Diseño moderno responsive (Inter + Sora)
├── js/
│   ├── data.js         # Seed — espejo de la semilla del backend
│   ├── api.js          # Cliente REST: intenta FastAPI, si no, motor local con LA MISMA interfaz
│   └── app.js          # Lógica de UI
└── backend/
    ├── main.py         # FastAPI + SQLite (auth HMAC, validación Pydantic, CORS, Swagger)
    └── requirements.txt
```

**Idea clave para entrevistas:** el frontend habla siempre con la misma API REST.
En GitHub Pages (sin servidor) un motor local responde con esa interfaz; en local,
levantas FastAPI y la demo se conecta sola a `http://localhost:8000` — el chip
superior cambia a «Backend FastAPI conectado 🟢».

## 🚀 Ejecutar el backend

```bash
cd demos/hogarhub/backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
# Swagger: http://localhost:8000/docs
```

## 🔌 API

| Método | Ruta | Auth | Descripción |
|---|---|---|---|
| GET | `/api/properties?q=&city=&type=&rooms=&max=` | — | Listar / buscar viviendas |
| GET | `/api/properties/{id}` | — | Detalle |
| POST | `/api/properties` | Bearer | Publicar vivienda |
| DELETE | `/api/properties/{id}` | Bearer | Eliminar vivienda |
| POST | `/api/auth/login` | — | Login → `{token, user}` |
| POST | `/api/contact` | — | Solicitar visita |
| GET | `/api/stats` | — | KPIs de la plataforma |

## 🛠️ Stack

Frontend HTML/CSS/JS (sin frameworks, para demostrar fundamentos) · FastAPI ·
SQLite · Pydantic · REST · Token auth · Canvas charts · localStorage ·
Responsive design. El mismo patrón API lo aplico en producción con
**Laravel + Vue.js** y en móvil con **Flutter**.

## 📄 Para mi CV (copiar/pegar)

- *Desarrollé HogarHub, plataforma inmobiliaria full-stack (FastAPI + SQLite + JS):
  buscador con filtros, auth por token, CRUD completo, calculadora hipotecaria y
  dashboard de estadísticas, desplegada en GitHub Pages.*
- *Diseñé una API REST con contrato único que funciona contra backend real o
  motor local, facilitando demos sin infraestructura.*
