# app/main.py — UNIFIED (fix: CORSMiddleware import + order)
import sys, importlib, logging
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware  # <-- LÉNYEGES!

log = logging.getLogger("airm-unified")
logging.basicConfig(level=logging.INFO)

BASE_DIR = Path(__file__).parent.resolve()            # app/
ROOT_DIR = BASE_DIR.parent.resolve()                  # repo gyökér
PUBLIC_DIR = (ROOT_DIR / "public").resolve()          # public/
AIRM_PKG_DIR = (BASE_DIR / "airm_module").resolve()   # app/airm_module

# import path guard
for p in (str(BASE_DIR), str(AIRM_PKG_DIR), str(ROOT_DIR)):
    if p not in sys.path:
        sys.path.insert(0, p)

app = FastAPI(title="AIRM Unified", version="2025.10.02", docs_url=None, redoc_url=None)

# --- CORS (szigorítható domain-listára) ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Health előre, hogy ne nyelje el a static mount ---
@app.get("/healthz")
def healthz():
    return {
        "ok": True,
        "public_exists": PUBLIC_DIR.is_dir(),
        "airm_mounted": bool(getattr(app, "_airm_mounted", False)),
    }

@app.get("/airm/healthz")
def airm_healthz():
    return {"ok": bool(getattr(app, "_airm_mounted", False))}

# --- AIRM subapp mount (/airm) ---
def try_mount_airm():
    try:
        mod = importlib.import_module("airm_module.main")
        sub = getattr(mod, "app", None)
        if sub is None:
            raise RuntimeError("airm_module.main nincs 'app' FastAPI instance")
        app.mount("/airm", sub)
        setattr(app, "_airm_mounted", True)
        log.info("Mounted AIRM at /airm")
    except Exception as e:
        setattr(app, "_airm_mounted", False)
        log.warning("AIRM module not mounted: %s", e)

try_mount_airm()

# --- Statikus site (/ → public/) ---
if PUBLIC_DIR.is_dir():
    app.mount("/static", StaticFiles(directory=str(PUBLIC_DIR)), name="static")

@app.get("/", include_in_schema=False)
def root_index():
    idx = PUBLIC_DIR / "index.html"
    if idx.is_file():
        return FileResponse(str(idx))
    return JSONResponse({"error": "index.html not found in /public"}, status_code=404)

if PUBLIC_DIR.is_dir():
    app.mount("/", StaticFiles(directory=str(PUBLIC_DIR), html=True), name="site")
    log.info("Mounted static site at / from %s", PUBLIC_DIR)
else:
    log.warning("public/ not found at %s", PUBLIC_DIR)
