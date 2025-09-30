import sys, importlib, pkgutil, pathlib
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from starlette.middleware.cors import CORSMiddleware

BASE_DIR = pathlib.Path(__file__).parent.resolve()
PUBLIC_DIR = (BASE_DIR.parent / "public").resolve()
AIRM_DIR = (BASE_DIR / "airm_module").resolve()
STATIC_DIR = (BASE_DIR.parent / "static").resolve()

# sys.path guards
for p in (str(BASE_DIR), str(AIRM_DIR), str(BASE_DIR.parent)):
    if p not in sys.path:
        sys.path.insert(0, p)

app = FastAPI(title="AIRM Monorepo")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def _find_airm_app():
    try:
        pkg = importlib.import_module("airm_module")
    except Exception:
        pkg = None

    def pick(mod):
        for attr in ("app","application"):
            cand = getattr(mod, attr, None)
            if cand and "fastapi.applications.FastAPI" in str(type(cand)):
                return cand
        return None

    if pkg:
        cand = pick(pkg)
        if cand: return cand
        for _, name, _ in pkgutil.walk_packages(pkg.__path__, prefix="airm_module."):
            try:
                mod = importlib.import_module(name)
                cand = pick(mod)
                if cand: return cand
            except Exception:
                continue

    for mn in ("airm_module.server","airm_module.main","airm_module.app"):
        try:
            mod = importlib.import_module(mn)
            cand = pick(mod)
            if cand: return cand
        except Exception:
            pass
    return None

AIRM_APP = _find_airm_app()

# --- UI bridge MUST be defined BEFORE mount, so it takes precedence
@app.get("/airm/ui", include_in_schema=False)
def airm_ui_bridge():
    return HTMLResponse(
        "<!doctype html><html lang='hu'><head><meta charset='utf-8'>"
        "<meta name='viewport' content='width=device-width,initial-scale=1'>"
        "<title>AIRM UI</title><style>html,body{height:100%;margin:0}iframe{width:100%;height:100%;border:0}</style>"
        "</head><body><iframe src='/airm/docs'></iframe></body></html>"
    )

# If no sub-app found, provide a tiny FastAPI so /airm/docs exists
if AIRM_APP is None:
    from fastapi import FastAPI as _F
    ph = _F(title="AIRM placeholder")
    @ph.get("/docs", include_in_schema=False)
    def _docs_redirect():
        return HTMLResponse("<p>AIRM modul nem importálható. Ellenőrizd az airm_module csomagot.</p>")
    AIRM_APP = ph

# --- Mount sub-app and statics
app.mount("/airm", AIRM_APP)
app.mount("/", StaticFiles(directory=str(PUBLIC_DIR), html=True), name="public")

if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR), html=False), name="extra_static")

@app.get("/healthz")
def healthz():
    return {"status":"ok","static": PUBLIC_DIR.is_dir(),"airm_mounted": True}
