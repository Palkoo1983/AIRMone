#!/usr/bin/env python3
import re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP_MAIN = ROOT / "app" / "main.py"
AIRM_MAIN = ROOT / "app" / "airm_module" / "main.py"
PUBLIC_DIR = ROOT / "app" / "public"

def read(p: Path) -> str:
    return p.read_text(encoding="utf-8")

def write(p: Path, s: str):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(s, encoding="utf-8")

def strip_diff_markers(text: str) -> str:
    out_lines = []
    for line in text.splitlines():
        # Remove git/patch markers
        if line.startswith('@@') or line.startswith('--- ') or line.startswith('+++ '):
            continue
        # Lines that are just patch +/- comments like "-# something" or "+# something"
        if re.match(r'^[\+\-]\s*#', line):
            cleaned = re.sub(r'^[\+\-]\s*', '', line)  # drop the +/-
            out_lines.append(cleaned)
            continue
        out_lines.append(line)
    return "\n".join(out_lines) + ("\n" if not text.endswith("\n") else "")

def ensure_import(html_resp_needed: bool, text: str) -> str:
    if html_resp_needed and "from fastapi.responses import HTMLResponse" not in text:
        lines = text.splitlines()
        # Insert after 'from fastapi import' if found, else prepend
        inserted = False
        for i, ln in enumerate(lines):
            if ln.strip().startswith("from fastapi import"):
                lines.insert(i+1, "from fastapi.responses import HTMLResponse")
                inserted = True
                break
        if not inserted:
            lines.insert(0, "from fastapi.responses import HTMLResponse")
        text = "\n".join(lines) + ("\n" if not text.endswith("\n") else "")
    return text

def ensure_typing_and_re(text: str) -> str:
    # Ensure typing Dict, etc.
    if "from typing import" in text and "Dict" not in text:
        text = text.replace("from typing import", "from typing import Any, Dict, List, Optional, Tuple, Set, Iterable, Union, Callable, ")
        text = text.replace("import  import", "import ")
    elif "from typing import" not in text:
        text = "from typing import Any, Dict, List, Optional, Tuple, Set, Iterable, Union, Callable\n" + text
    # Ensure 'import re' if 're.' is used
    if re.search(r'(^|\n)\s*import re(\s|$)', text) is None and "re." in text:
        text = "import re\n" + text
    return text

def ensure_healthz_before_mounts(text: str) -> str:
    # Ensure /healthz exists
    if "/healthz" not in text:
        health = (
            "\n\n# ---- HEALTH ENDPOINT (must be before mounts) ----\n"
            "@app.get('/healthz')\n"
            "def healthz():\n"
            "    from pathlib import Path as _P\n"
            "    PUBLIC_DIR = (_P(__file__).parent / 'public').resolve()\n"
            "    return {'ok': True, 'public_exists': PUBLIC_DIR.is_dir()}\n"
        )
        text += health

    # Move mounts after healthz
    lines = text.splitlines()
    mount_lines = []
    kept_lines = []
    for ln in lines:
        if re.search(r'\bapp\.mount\(\s*["\'](/|/airm)', ln):
            mount_lines.append(ln)
        else:
            kept_lines.append(ln)
    airms = [m for m in mount_lines if '"/airm"' in m or "'/airm'" in m]
    roots = [m for m in mount_lines if '"/"' in m or "'/'" in m]
    new_text = "\n".join(kept_lines).rstrip() + "\n"
    if airms:
        new_text += "\n# ---- Mount AIRM ----\n" + "\n".join(airms) + "\n"
    if roots:
        new_text += "\n# ---- Mount static root ----\n" + "\n".join(roots) + "\n"
    return new_text

def patch_app_main():
    if not APP_MAIN.exists():
        print(f"[skip] {APP_MAIN} nem található.")
        return
    t = read(APP_MAIN)
    t = strip_diff_markers(t)
    t = ensure_healthz_before_mounts(t)
    write(APP_MAIN, t)
    print(f"[ok] Patchelve: {APP_MAIN}")

def patch_airm_main():
    if not AIRM_MAIN.exists():
        print(f"[skip] {AIRM_MAIN} nem található.")
        return
    t = read(AIRM_MAIN)
    t = strip_diff_markers(t)
    t = ensure_typing_and_re(t)
    t = ensure_import(True, t)  # HTMLResponse szükséges
    write(AIRM_MAIN, t)
    print(f"[ok] Patchelve: {AIRM_MAIN}")

def ensure_public_index():
    if not PUBLIC_DIR.exists():
        return
    index = PUBLIC_DIR / "index.html"
    if not index.exists():
        index.write_text("<!doctype html><meta charset='utf-8'><title>AIRM unified</title><h1>AIRM unified</h1><p><a href='/airm/docs'>AIRM API docs</a></p>", encoding="utf-8")
        print(f"[ok] Létrehozva: {index}")

def main():
    patch_app_main()
    patch_airm_main()
    ensure_public_index()
    print("[done] Kész. Állítsd a Render Health Check Path-ot: /healthz")

if __name__ == "__main__":
    main()
