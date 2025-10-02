# app/main.py — UNIFIED entrypoint (static site + optional AIRM subapp)
import os
import sys
import logging
import importlib
from pathlib import Path
from typing import Optional

from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

# ------------------------------------------------------------------------------
# Paths & logging
# ------------------------------------------------------------------------------
logging.basicConfig(level=logging.INFO)
log = logging.getLogger("airm-unified")

BASE_DIR: Path = Path(__file__).parent.resolve()          # .../app
ROOT_DIR: Path = BASE_DIR.parent.resolve()                 # repo root
PUBLIC_DIR: Path = (ROOT_DIR / "public").resolve()         # .../public
AIRM_PKG_DIR: Path = (BASE_DIR / "airm_module").resolve()  # .../app/airm_module

# Ensure import paths (idempotent)
for p in (str(BASE_DIR), str(AIRM_PKG_DIR), str(ROOT_DIR)):
    if p not in sys.path:
        sys.path.insert(0, p)

# ------------------------------------------------------------------------------
# Main FastAPI app
# ------------------------------------------------------------------------------
app = FastAPI(
    title="AIRM Unified",
    version="2025.10.02",
    docs_url=None,     # fő app Swagger kikapcs, hogy ne ütközzön a statikus gyökérrel
    redoc_url=None,
)

# CORS (szigorítható domain-listára)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------------------------------------------------------------------
# Health endpoints (ELŐBB, hogy ne nyelje el a "/" mount)
# ------------------------------------------------------------------------------
@app.get("/healthz")
def healthz():
    return {
        "ok": True,
        "public_exists": PUBLIC_DIR.is_dir(),
        "airm_module_dir": str(AIRM_PKG_DIR),
        "airm_mounted": hasattr(app, "_airm_mounted") and bool(getattr(app, "_airm_mounted")),
    }

# opcionális: külön AIRM health, akkor is ad választ, ha nincs mount
@app.get("/airm/healthz")
def airm_healthz():
    mounted = hasattr(app, "_airm_mounted") and bool(getattr(app, "_airm_mounted"))
    return {"ok": mounted}

# ------------------------------------------------------------------------------
# Try to import & mount AIRM sub-application under /airm (optional)
# ------------------------------------------------------------------------------
def try_mount_airm() -> Optional[FastAPI]:
    """
    Tries to import app/airm_module/main.py and get `app` from it.
    On success, mounts it under /airm and returns the subapp, else None.
    """
    try:
        airm_module = importlib.import_module("airm_module.main")
    except Exception as e:
        log.warning("AIRM module not found or failed to import: %s", e)
        setattr(app, "_airm_mounted", False)
        return None

    subapp = getattr(airm_module, "app", None)
    if subapp is None:
        log.error("airm_module.main does not expose `app` FastAPI instance.")
        setattr(app, "_airm_mounted", False)
        return None

    # Mount only once
    if not (hasattr(app, "_airm_mounted") and getattr(app, "_airm_mounted")):
        app.mount("/airm", subapp)
        setattr(app, "_airm_mounted", True)
        log.info("Mounted AIRM subapp at /airm")
    return subapp

try_mount_airm()

# ------------------------------------------------------------------------------
# Static site: serve /public as root (multi-page HTML)
# ------------------------------------------------------------------------------
# /static -> assets (CSS/JS/images) same dir as public: convenience alias
if PUBLIC_DIR.is_dir():
    app.mount("/static", StaticFiles(directory=str(PUBLIC_DIR)), name="static")
else:
    log.warning("Public dir does not exist: %s", PUBLIC_DIR)

# Root route: serve index.html if exists (explicit endpoint)
@app.get("/", include_in_schema=False)
def root_index():
    index_path = PUBLIC_DIR / "index.html"
    if index_path.is_file():
        return FileResponse(str(index_path))
    return JSONResponse({"error": "index.html not found in /public"}, status_code=404)

# Mount the whole public folder for multi-page HTML (AFTER health routes!)
if PUBLIC_DIR.is_dir():
    # html=True → index.html + clean URLs működnek
    app.mount("/", StaticFiles(directory=str(PUBLIC_DIR), html=True), name="site")
    log.info("Mounted static site at / from %s", PUBLIC_DIR)
else:
    log.warning("Skipping static mount because public/ not found at: %s", PUBLIC_DIR)

# ------------------------------------------------------------------------------
# Optional debug: show resolved paths (helpful in Render logs)
# ------------------------------------------------------------------------------
@app.get("/_debug/paths")
def debug_paths():
    return {
        "BASE_DIR": str(BASE_DIR),
        "ROOT_DIR": str(ROOT_DIR),
        "PUBLIC_DIR": str(PUBLIC_DIR),
        "AIRM_PKG_DIR": str(AIRM_PKG_DIR),
        "sys.path_head": sys.path[:5],
    }
