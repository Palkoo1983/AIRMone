# app/main.py  — CLEAN

from pathlib import Path
import importlib
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

logging.basicConfig(level=logging.INFO)

app = FastAPI(
    title="AIRM unified",
    docs_url=None,
    redoc_url=None,
)

# CORS – ha kell szigorítani, itt tedd meg
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)

PUBLIC_DIR = (Path(__file__).parent / "public").resolve()

# ---- HEALTH ENDPOINTS ELŐSZÖR! (hogy ne nyelje el a "/" static mount) ----
@app.get("/healthz")
def healthz():
    return {
        "ok": True,
        "public_exists": PUBLIC_DIR.is_dir(),
    }

# ---- AIRM betöltés és mount ----
airm_module = importlib.import_module("airm_module.main")
airm_app = getattr(airm_module, "app")
app.mount("/airm", airm_app)

# ---- Statikus site a gyökéren (ha van public/) ----
if PUBLIC_DIR.is_dir():
    app.mount("/", StaticFiles(directory=str(PUBLIC_DIR), html=True), name="site")

import pathlib, sys, importlib
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.cors import CORSMiddleware

BASE_DIR = pathlib.Path(__file__).parent.resolve()
PUBLIC_DIR = (BASE_DIR.parent / "public").resolve()
AIRM_PKG_DIR = (BASE_DIR / "airm_module").resolve()

# import path guard
for p in (str(BASE_DIR), str(AIRM_PKG_DIR), str(BASE_DIR.parent)):
    if p not in sys.path:
        sys.path.insert(0, p)

# 1) AIRM alapp alkalmazás betöltése a meglévő modulból
#    Fontos: app/airm_module/main.py-ben legyen: `app = FastAPI(...)`
airm_module = importlib.import_module("airm_module.main")
airm_app = getattr(airm_module, "app", None)
if airm_app is None:
    raise RuntimeError("airm_module.main nem tartalmaz 'app' FastAPI objektumot")

# 2) Fő integrátor app
app = FastAPI(title="AIRM Unified", version="2025.10.02")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # ha szigorítanád: konkrét domain lista
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
-# /airm -> AIRM API
-app.mount("/airm", airm_app)

-# / -> statikus web
-app.mount("/", StaticFiles(directory=str(PUBLIC_DIR), html=True), name="site")

-# Egészség-ellenőrzések
-@app.get("/healthz")
-def healthz():
-    return {"ok": True, "public_exists": PUBLIC_DIR.is_dir(), "airm_mounted": True}

-@app.get("/airm/healthz")
-def airm_healthz():
-    return {"ok": True}

+# Egészség-ellenőrzések (ELŐBB!)
+@app.get("/healthz")
+def healthz():
+    return {"ok": True, "public_exists": PUBLIC_DIR.is_dir(), "airm_mounted": True}

+@app.get("/airm/healthz")
+def airm_healthz():
+    return {"ok": True}

+# /airm -> AIRM API
+app.mount("/airm", airm_app)

+# / -> statikus web
+app.mount("/", StaticFiles(directory=str(PUBLIC_DIR), html=True), name="site")

# /airm -> AIRM API (docs: /airm/docs, openapi: /airm/openapi.json)
app.mount("/airm", airm_app)

# / -> statikus web (public/), multi-page HTML kiszolgálással
# fontos: public/index.html, public/*.html fájlok
app.mount("/", StaticFiles(directory=str(PUBLIC_DIR), html=True), name="site")

# Egyszerű egészség-ellenőrző végpontok
@app.get("/healthz")
def healthz():
    return {
        "ok": True,
        "public_exists": PUBLIC_DIR.is_dir(),
        "airm_mounted": True
    }

@app.get("/airm/healthz")
def airm_healthz():
    return {"ok": True}
