import os, sys, importlib, pkgutil, pathlib
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from starlette.middleware.cors import CORSMiddleware

BASE_DIR = pathlib.Path(__file__).parent.resolve()
PUBLIC_DIR = (BASE_DIR.parent / "public").resolve()
AIRM_DIR = (BASE_DIR / "airm_module").resolve()

# import pathok
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

def _find_airm_app():
    try:
        pkg = importlib.import_module("airm_module")
    except Exception:
        pkg = None
    # közvetlenül a csomagban
    if pkg:
        for attr in ("app", "application"):
            cand = getattr(pkg, attr, None)
            if str(type(cand)).endswith("fastapi.applications.FastAPI'>"):
                return cand
        # almodulok bejárása
        for _, name, _ in pkgutil.walk_packages(pkg.__path__, prefix="airm_module."):
            try:
                mod = importlib.import_module(name)
            except Exception:
                continue
            for attr in ("app", "application"):
                cand = getattr(mod, attr, None)
                if str(type(cand)).endswith("fastapi.applications.FastAPI'>"):
                    return cand
    # ismert modulnevek
    for mn in ("airm_module.server", "airm_module.main", "airm_module.app"):
        try:
            mod = importlib.import_module(mn)
            for attr in ("app", "application"):
                cand = getattr(mod, attr, None)
                if str(type(cand)).endswith("fastapi.applications.FastAPI'>"):
                    return cand
        except Exception:
            pass
    return None

AIRM_APP = _find_airm_app()

# --- 1) ELŐSZÖR az AIRM mount (/airm), hogy ne nyelje el a static "/"
if AIRM_APP is None:
    from fastapi import FastAPI as _F
    ph = _F(title="AIRM placeholder")
    @ph.get("/ui")
    def ui_placeholder():
        return HTMLResponse("<h3>AIRM modul nem importálható.</h3>"
                            "<p>Ellenőrizd, hogy az <code>app/airm_module</code> alatt van-e FastAPI <code>app</code>.</p>")
    @ph.get("/healthz")
    def ph_healthz():
        return {"airm": "missing"}
    AIRM_APP = ph

app.mount("/airm", AIRM_APP)

# --- 2) UTÁNA a statikus site a gyökről
app.mount("/", StaticFiles(directory=str(PUBLIC_DIR), html=True), name="static")

# Health
@app.get("/healthz")
def healthz():
    return {"status": "ok", "static": PUBLIC_DIR.is_dir(), "airm_mounted": True}

# Biztos fallback /ellenorzes.html ha a fájl hiányozna
ELLEN_HTML = """<!doctype html><html lang="hu"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Kockázatelemzés 1 perc alatt</title>
<style>html,body{height:100%;margin:0} header{padding:12px 16px;border-bottom:1px solid #eee;font:16px system-ui}
.wrap{height:calc(100% - 53px)} iframe{width:100%;height:100%;border:0}</style></head>
<body><header>Kockázatelemzés 1 perc alatt</header>
<div class="wrap"><iframe src="/airm/ui" title="AIRM modul"></iframe></div></body></html>"""
@app.get("/ellenorzes.html")
def ellenorzes_fallback():
    f = PUBLIC_DIR / "ellenorzes.html"
    if f.exists():
        # StaticFiles úgyis kiszolgálná, de adjuk vissza biztosra:
        return HTMLResponse(f.read_text(encoding="utf-8", errors="ignore"))
    return HTMLResponse(ELLEN_HTML)
