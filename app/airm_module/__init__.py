# app/airm_module/__init__.py
# Shim: biztosítsuk, hogy legyen exportált FastAPI `app` és azon /ui route

from typing import Optional

app: Optional["FastAPI"] = None  # type: ignore

def _try_import():
    global app
    # 1) server.py
    try:
        from .server import app as _app  # type: ignore
        app = _app
        return
    except Exception:
        pass
    # 2) main.py
    try:
        from .main import app as _app  # type: ignore
        app = _app
        return
    except Exception:
        pass
    # 3) app.py
    try:
        from .app import app as _app  # type: ignore
        app = _app
        return
    except Exception:
        pass

_try_import()

# Ha nem talált app-ot, adjunk egy beszédes placeholdert /ui route-tal,
# így az iframe legalább jelezni tudja a konkrét problémát.
if app is None:
    from fastapi import FastAPI
    from fastapi.responses import HTMLResponse

    app = FastAPI(title="AIRM placeholder (import shim)")

    @app.get("/ui")
    def _ui():
        return HTMLResponse(
            "<h3>AIRM modul nem importálható.</h3>"
            "<p>Nem található FastAPI <code>app</code> a "
            "<code>server.py</code> / <code>main.py</code> / <code>app.py</code> fájlban.</p>"
        )

    @app.get("/healthz")
    def _hz():
        return {"airm": "missing"}

# Utolsó védőháló: ha találtunk app-ot, de nincs /ui útvonal, tegyünk rá egyet,
# hogy az iframe biztosan kapjon választ, és jelentsük ki az okot.
else:
    try:
        has_ui = any(getattr(r, "path", "") == "/ui" for r in getattr(app, "routes", []))  # type: ignore
    except Exception:
        has_ui = False

    if not has_ui:
        from fastapi.responses import HTMLResponse

        @app.get("/ui")  # type: ignore
        def _missing_ui():
            return HTMLResponse(
                "<h3>AIRM app megvan, de nincs <code>/ui</code> route.</h3>"
                "<p>Add hozzá az AIRM appodhoz, vagy hagyd ezt a fallbacket ideiglenesen.</p>"
            )
