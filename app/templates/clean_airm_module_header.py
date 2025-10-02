from pathlib import Path
import json, math, re
from typing import Any, Dict, List, Optional, Tuple, Set, Iterable, Union, Callable

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse

app = FastAPI(title="AIRM backend", version="2025.10.02", docs_url="/docs", openapi_url="/openapi.json", redoc_url=None)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

STATIC_DIR = (Path(__file__).parent / "static").resolve()
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="airm_static")
# --- innen folytatódik a modul saját kódja ---
