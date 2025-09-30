import os, sys, importlib, pkgutil, pathlib
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from starlette.middleware.cors import CORSMiddleware

BASE_DIR = pathlib.Path(__file__).parent.resolve()
PUBLIC_DIR = (BASE_DIR.parent / "public").resolve()
AIRM_DIR = (BASE_DIR / "airm_module").resolve()

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

def _has_ui_route(fapp: FastAPI) -> bool:
    try:
        for r in getattr(fapp, "routes", []):
            if getattr(r, "path", "") == "/ui":
                return True
    except Exception:
        pass
    return False

def _find_airm_app() -> FastAPI | None:
    try:
        pkg = importlib.import_module("airm_module")
    except Exception:
        pkg = None

    def _pick_from_module(mod) -> FastAPI | None:
        for attr in ("app", "application"):
            cand = getattr(mod, attr, None)
            if isinstance(cand, FastAPI) and _has_ui_route(cand):
                return cand
        return None

    # 1) közvetlenül airm_module
    if pkg:
        cand = _pick_from_module(pkg)
        if cand: return cand

        # 2) almodulok bejárása
        for _, name, _ in pkgutil.walk_packages(pkg.__path__, prefix="airm_module."):
            try:
                mod = importlib.import_module(name)
            except Exception:
                continue
            cand = _pick_from_module(mod)
            if cand: return cand

    # 3) kézzel ismert nevek
    for mn in ("airm_module.server", "airm_module.main", "airm_module.app"):
        try:
            mod = importlib.import_module(mn)
            cand = _pick_from_module(mod)
            if cand: return cand
        except Exception:
            pass

    return None

AIRM_APP = _find_airm_app()

# --- 1) ELŐBB az AIRM mount (/airm)
if AIRM_APP is None:
    ph = FastAPI(title="AIRM placeholder")
    @ph.get("/ui")
    def ui_placeholder():
        return HTMLResponse(
            "<h3>AIRM modul nem importálható vagy nincs /ui route.</h3>"
            "<p>Ellenőrizd, hogy az <code>app/airm_module</code> alatt van-e FastAPI <code>app</code> és azon <code>/ui</code> útvonal.</p>"
        )
    @ph.get("/healthz")
    def ph_healthz():
        return {"airm": "missing"}
    AIRM_APP = ph

# debug: listázd az AIRM al-app route-jait
@AIRM_APP.get("/routes")
def airm_routes():
    try:
        return [getattr(r, "path", "") for r in getattr(AIRM_APP, "routes", [])]
    except Exception:
        return []
# --- UI-bridge: saját /airm/ui a fő appban, hogy mindig legyen látható UI.
from fastapi.responses import HTMLResponse

@app.get("/airm/ui", include_in_schema=False)
def airm_ui_bridge():
    # ha az AIRM al-app docs elérhető, azt ágyazzuk be; különben egyszerű tesztoldal
    html = """
    <!doctype html><html lang="hu"><head><meta charset="utf-8">
    <meta name="viewport" content="width=device-width,initial-scale=1">
    <title>AIRM UI</title>
    <style>html,body{height:100%;margin:0} iframe{width:100%;height:100%;border:0}</style>
    </head><body>
      <iframe src="/airm/docs" title="AIRM Docs"></iframe>
    </body></html>
    """
    return HTMLResponse(html)
app.mount("/airm", AIRM_APP)

# --- 2) statikus site a gyökről
app.mount("/", StaticFiles(directory=str(PUBLIC_DIR), html=True), name="static")

# --- 3) extra /static mount (ha van külön static mappa)
STATIC_DIR = (BASE_DIR.parent / "static").resolve()
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR), html=False), name="extra_static")

# Health
@app.get("/healthz")
def healthz():
    return {"status": "ok", "static": PUBLIC_DIR.is_dir(), "airm_mounted": True}
