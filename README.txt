# AIRM Monorepo — Render READY (Static site + AIRM module)

**Egyben deployolható** csomag Renderre. A statikus weboldal a `public/` mappából szolgálódik ki,
az AIRM FastAPI modul a `/airm` útvonal alatt érhető el. A "Kockázatelemzés 1 perc alatt"
lap iframe-ben a `/airm/ui` felületet tölti be.

## Struktúra
- `public/` – a statikus weboldal (index.html és társai)
- `app/`
  - `main.py` – FastAPI indító, ami a `public/` tartalmat és az AIRM modult is kiszolgálja
  - `airm_module/` – az AIRM Render modul teljes forrása (beágyazva)
  - `requirements.txt` – Python függőségek
- `render.yaml` – Render deploy leírás

## Lokális futtatás (Windows)
```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r app\requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000
```
Nyisd meg: <http://127.0.0.1:8000/index.html> vagy <http://127.0.0.1:8000/ellenorzes.html>  
Az AIRM UI: <http://127.0.0.1:8000/airm/ui>

## Render deploy
- Hozz létre új **Web Service**-t, GitHub repóból vagy ZIP-ből.
- Build command: `pip install -r app/requirements.txt`
- Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- Health check path: `/healthz`

Kész. A "Kockázatelemzés" oldal az `/airm/ui`-t fogja betölteni iframe-ben.
