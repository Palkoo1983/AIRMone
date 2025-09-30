import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.responses import FileResponse, Response
from starlette.middleware.cors import CORSMiddleware

# === Serve static site from ../public ===
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PUBLIC_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", "public"))

app = FastAPI(title="AIRM Monorepo (Static + AIRM module)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files at root
app.mount("/", StaticFiles(directory=PUBLIC_DIR, html=True), name="static")

# Import and mount AIRM FastAPI app under /airm
# We attempt to import app object from the discovered module.
AIRM_APP = None
ERR = None
try:
    # Try common import paths
    # 1) airn_module.server:app
    from airm_module import server as airm_server
    AIRM_APP = getattr(airm_server, "app", None)
except Exception as e1:
    ERR = e1

if AIRM_APP is None:
    try:
        from airm_module import main as airm_main
        AIRM_APP = getattr(airm_main, "app", None)
    except Exception as e2:
        ERR = e2

if AIRM_APP is None:
    # last resort: search dynamically for an app object
    AIRM_APP = FastAPI(title="AIRM placeholder")
    @AIRM_APP.get("/ui")
    def ui_placeholder():
        return {"status": "error", "message": "AIRM app not found/import failed", "error": str(ERR) if ERR else "unknown"}

app.mount("/airm", AIRM_APP)

# Health check
@app.get("/healthz")
def healthz():
    return {"status": "ok", "static": os.path.isdir(PUBLIC_DIR)}