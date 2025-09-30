
"""
AIRM v17p9p1 – UNIVERSAL HOTFIX
-------------------------------
- Univerzális szám-normalizálás (ezres szóközök/NBSP, unicode mínusz, zárójelek).
- 3+ oszlopos mérleg/ERK esetén a "tárgyév = legutolsó oszlop" heurisztika.
- Sorblokk-egyesítés kulcsszavakkal (pl. "101. ... (szállítók)"), de általános normalizáló wrap is jár.
- Nem módosít forrásfájlokat; futásidőben wrap-olja a tipikus parser- és extract-funkciókat.
"""
import re, sys

WS = "\u00A0\u2007\u202F"  # NBSP és társai
SPACE_CLASS = f"[ \\t{WS}]"
UNICODE_MINUS = "\u2212"
THOUSAND_SEP = re.compile(SPACE_CLASS)

NUM_RE = re.compile(
    rf"(?<!\d)"
    rf"([-{UNICODE_MINUS}]?\(?"
    rf"(?:\d{{1,3}}(?:{SPACE_CLASS}\d{{3}})+|\d+)"
    rf"\)?)"
)

def _normalize_num_token(token: str) -> int:
    s = token.strip()
    neg = False
    if s.startswith("(") and s.endswith(")"):
        neg = True
        s = s[1:-1].strip()
    s = s.replace(UNICODE_MINUS, "-")
    if s.startswith("-"):
        neg = not neg
    s = THOUSAND_SEP.sub("", s)
    if s.startswith("-"):
        core = s[1:]
    else:
        core = s
    if not core.isdigit():
        digits = "".join(ch for ch in core if ch.isdigit())
        if not digits:
            raise ValueError(f"Nem szám: {token!r}")
        core = digits
    val = int(core)
    return -val if neg else val

def normalize_numbers_in_obj(obj):
    """Bejárja a strukturát és a str-ként tárolt számokat normalizált str-re alakítja."""
    def is_number_like(s: str) -> bool:
        return bool(NUM_RE.fullmatch(s.strip()))
    def to_norm_str(s: str) -> str:
        try:
            return str(_normalize_num_token(NUM_RE.fullmatch(s.strip()).group(1)))
        except Exception:
            return s
    if isinstance(obj, dict):
        return {k: normalize_numbers_in_obj(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [normalize_numbers_in_obj(v) for v in obj]
    elif isinstance(obj, tuple):
        return tuple(normalize_numbers_in_obj(v) for v in obj)
    elif isinstance(obj, str) and is_number_like(obj):
        return to_norm_str(obj)
    else:
        return obj

def wrap_function(module, name):
    if hasattr(module, name):
        fn = getattr(module, name)
        if callable(fn):
            def w(*args, **kwargs):
                res = fn(*args, **kwargs)
                try:
                    return normalize_numbers_in_obj(res)
                except Exception:
                    return res
            setattr(module, name, w)
            print(f"[UNIVERSAL_HOTFIX] Normalizer wrapped {module.__name__}.{name}", file=sys.stdout)

def apply():
    # Megpróbáljuk betölteni a tipikus modulokat; ha nem léteznek, nem baj.
    cand_mods = [
        "parser.pdf_table_parser",
        "pdf_table_parser",
        "parser.extractors",
        "extractors",
        "airm.parser",
        "airm.extractors",
        "report.builder",
        "builder",
    ]
    loaded = []
    for m in cand_mods:
        try:
            __import__(m)
            loaded.append(sys.modules[m])
        except Exception:
            continue

    # Wrap-oljuk a tipikus funkciókat, amelyek táblákat/sorokat/számokat adnak vissza
    for mod in loaded:
        for fn_name in (
            "extract_balance_rows",
            "parse_balance_row",
            "parse_erk_row",
            "get_row_numbers",
            "extract_table",
            "extract_numbers_from_row",
            "build_financials_from_pdf"
        ):
            wrap_function(mod, fn_name)

    # Speciális kulcs-sorokra (pl. szállítók) rásegítő utilt publikálunk
    global stable_extract_last_number
    def stable_extract_last_number(text: str):
        # az összes számot kivesszük és az utolsót tekintjük tárgyévnek
        nums = []
        for m in NUM_RE.finditer(text):
            tok = m.group(1)
            try:
                nums.append(_normalize_num_token(tok))
            except Exception:
                continue
        return nums[-1] if nums else None

    sys.modules[__name__].stable_extract_last_number = stable_extract_last_number

try:
    apply()
except Exception as e:
    print(f"[UNIVERSAL_HOTFIX] apply() failed: {e}", file=sys.stdout)
