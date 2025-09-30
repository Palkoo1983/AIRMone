from typing import Optional

app: Optional["FastAPI"] = None  # type: ignore

def _try_import():
    global app
    try:
        from .server import app as _app  # type: ignore
        app = _app; return
    except Exception:
        pass
    try:
        from .main import app as _app  # type: ignore
        app = _app; return
    except Exception:
        pass
    try:
        from .app import app as _app  # type: ignore
        app = _app; return
    except Exception:
        pass

_try_import()
