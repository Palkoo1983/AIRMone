import os, sys, importlib, pkgutil, types, pathlib
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, HTMLResponse
from starlette.middleware.cors import CORSMiddleware

BASE_DIR = pathlib.Path(__file__).parent.resolve()
PUBLIC_DIR = (BASE_DIR.parent / "public").resolve()
AIRM_DIR = (BASE_DIR / "airm_module").resolve()

# Biztosítsuk, hogy az airm_module importálható legyen
for p in [str(BASE_DIR), str(AIRM_DIR), str(BASE_DIR.parent)]:
    if p not in sys.path:
        sys.path.insert(0, p)

app = FastAPI(title="AIRM Monorepo (Static + AIRM module)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Static site a gyökéren
app.mount("/", StaticFiles(directory=str(PUBLIC_DIR), html=True), name="static")

def _find_airm_app() -> FastAPI | None:
    """
    Dinamikusan megpróbál egy FastAPI 'app' objektumot találni az airm_module csomagban.
    Elfogadjuk a 'server.py', 'main.py', 'app.py' stb. modulok app-ját.
    """
    try:
        pkg = importlib.import_module("airm_module")
    except Exception:
        return None

    # 1) Ha közvetlenül airm_module.app létezik
    for attr in ("app", "application"):
        if hasattr(pkg, attr) and isinstance(getattr(pkg, attr), FastAPI):
            return getattr(pkg, attr)

    # 2) Almodulok bejárása és 'app' keresése
    for finder, name, ispkg in pkgutil.walk_packages(pkg.__path__, prefix="airm_module."):
        try:
            mod = importlib.import_module(name)
        except Exception:
            continue
        for attr in ("app", "application"):
            candidate = getattr(mod, attr, None)
            if isinstance(candidate, FastAPI):
                return candidate

    # 3) Közismert fájlnevek megpróbálása közvetlen importtal
    for mn in ["airm_module.server", "airm_module.main", "airm_module.app"]:
        try:
            mod = importlib.import_module(mn)
            for attr in ("app", "application"):
                candidate = getattr(mod, attr, None)
                if isinstance(candidate, FastAPI):
                    return candidate
        except Exception:
            pass

    return None

AIRM_APP = _find_airm_app()

# Ha nem található, csináljunk egy beszédes placeholdert
if AIRM_APP is None:
    placeholder = FastAPI(title="AIRM placeholder")
    @placeholder.get("/ui")
    def ui_placeholder():
        return HTMLResponse(
            "<h3>AIRM modul nem importálható.</h3>"
            "<p>Ellenőrizd, hogy az <code>app/airm_module</code> alatt van-e egy "
            "FastAPI <code>app</code> objektum (pl. server.py vagy main.py).</p>"
        )
    @placeholder.get("/healthz")
    def ph_healthz():
        return {"airm": "missing"}

    AIRM_APP = placeholder

# AIRM mount /airm alatt
app.mount("/airm", AIRM_APP)

# Monorepo health
@app.get("/healthz")
def healthz():
    return {"status": "ok", "static": PUBLIC_DIR.is_dir(), "airm_mounted": AIRM_APP is not None}
