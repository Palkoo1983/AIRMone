# AIRM Render Fix Kit

Ez a csomag segít a `Deploying…`/`Timed Out` és `SyntaxError: invalid syntax` hibák javításában,
amik diff-jelölők (`-`, `+`, `@@`, `---`, `+++`) és hiányzó importok miatt jelennek meg.

## Használat (ajánlott - automatikus patch)
1. Másold ezt a ZIP-et a projekt gyökerébe (ahol az `app/` mappa van).
2. Futtasd:  
   ```bash
   python3 scripts/patch_render_fix.py
   ```
3. Commit → Push → Render redeploy.
4. Render beállítás: **Health Check Path = `/healthz`**.

A patch script NEM törli a logikádat; a következőket csinálja:
- Eltávolítja a diff-jelző sorokat az `app/main.py` és `app/airm_module/main.py` fájlokból.
- Hozzáadja a hiányzó `HTMLResponse` importot az AIRM modulhoz.
- Biztosítja, hogy legyen `/healthz` endpoint.
- A `app/main.py`-ban a health endpointot a mountok elé teszi, hogy a Render health check biztosan 200-at kapjon.
- A `public/index.html` hiányában nem kötelező, de ha van `public/`, akkor a statikus mount megmarad.

## Alternatíva (kézi)
- Nézd meg a `templates/clean_app_main.py` és `templates/clean_airm_module_header.py` fájlokat mintának,
  és kézzel igazítsd a saját fájljaidat.

Sok sikert! 🚀
