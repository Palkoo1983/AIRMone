from pathlib import Path
import importlib
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

app = FastAPI(title="AIRM unified", docs_url=None, redoc_url=None)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)

PUBLIC_DIR = (Path(__file__).parent / "public").resolve()

@app.get("/healthz")
def healthz():
    return {"ok": True, "public_exists": PUBLIC_DIR.is_dir()}

airm_module = importlib.import_module("airm_module.main")
airm_app = getattr(airm_module, "app")
app.mount("/airm", airm_app)

if PUBLIC_DIR.is_dir():
    app.mount("/", StaticFiles(directory=str(PUBLIC_DIR), html=True), name="site")
