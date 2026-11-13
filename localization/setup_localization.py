"""Metadata + UI localization (French / German) for the Ecommerce (Conference) workspaces.

What it does (idempotent, safe to re-run):
  1. For every Conference workspace that owns objects (the parent, and Blessing Health System for its own extras),
     exports the XLIFF for fr-FR and de-DE, fills in the <target> elements from
     translations/<locale>.json and uploads it (translations/set).
  2. Sets the LOCALE (UI) and METADATA_LOCALE (titles/descriptions) workspace settings according to
     WORKSPACE_LOCALES below. Children inherit from the parent unless they set their own value.

Usage:
  python3 localization/setup_localization.py              # translations + workspace settings
  python3 localization/setup_localization.py --only translations
  python3 localization/setup_localization.py --only settings
  python3 localization/setup_localization.py --reset      # back to en-US: removes settings + translations

Re-run the translations step after editing any title/description: GoodData drops the translation of a
string whenever its English source changes. New strings are reported as "missing" (left in English) —
add them to translations/<locale>.json.
"""
import argparse, copy, json, pathlib, sys
import xml.etree.ElementTree as ET

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from _gd import call  # noqa: E402

HERE = pathlib.Path(__file__).parent
LOCALES = ["fr-FR", "de-DE"]

PARENT = "gdc_demo_a7c3afa0-ca91-40db-a3a8-df4d5044e92f"
WORKSPACES = {
    PARENT: "Ecommerce (Conference)",
    "gdc_demo_86a46377-cad8-4c3d-ab7c-6ba753b49b2c": "Edgewood College",
    "gdc_demo_9df6e6ad-de8a-42e3-9893-f13abe01e203": "Ohio Statehouse",
    "gdc_demo_c8e457e4-64e9-4226-b2d7-b914e5f260b5": "Blessing Health System",
}
# Which language each tenant shows. None = inherit (parent/org default, en-US).
WORKSPACE_LOCALES = {
    # Edgewood stays English by default; fr-FR / de-DE translations are loaded so it can be switched.
    "gdc_demo_9df6e6ad-de8a-42e3-9893-f13abe01e203": "de-DE",  # Ohio Statehouse -> German
    "gdc_demo_c8e457e4-64e9-4226-b2d7-b914e5f260b5": "de-DE",  # Blessing Health System -> German
}
SETTING_TYPES = ["LOCALE", "METADATA_LOCALE"]

NS = "urn:oasis:names:tc:xliff:document:2.0"
ET.register_namespace("", NS)
q = lambda tag: f"{{{NS}}}{tag}"
JSON = dict(ctype="application/json", accept="*/*")


def source_text(src):
    return (src.text or "") + "".join(c.tail or "" for c in src)


def fill_xliff(raw: bytes, mapping: dict):
    root = ET.fromstring(raw)
    done = missing = 0
    for seg in root.iter(q("segment")):
        src = seg.find(q("source"))
        text = source_text(src)
        if not text.strip():
            continue
        tr = mapping.get(text)
        if not tr:
            missing += 1
            continue
        old = seg.find(q("target"))
        if old is not None:
            seg.remove(old)
        tgt = ET.SubElement(seg, q("target"))
        # keep the inline path markers (<mrk .../>) of free-form strings, then the translated text
        tgt.text = src.text if src.text and not src.text.strip() else None
        for child in src:
            m = copy.deepcopy(child)
            m.tail = None
            tgt.append(m)
        if len(tgt):
            tgt[-1].tail = tr
        else:
            tgt.text = tr
        done += 1
    return ET.tostring(root, encoding="utf-8", xml_declaration=True), done, missing


def push_translations():
    for loc in LOCALES:
        mapping = json.loads((HERE / "translations" / f"{loc}.json").read_text())
        for ws, name in WORKSPACES.items():
            raw = call("POST", f"/api/v1/actions/workspaces/{ws}/translations/retrieve", {"locale": loc}, raw=True, **JSON)
            body, done, missing = fill_xliff(raw, mapping)
            if not done:
                print(f"  {loc} {name}: nothing owned here (inherits parent translations)")
                continue
            call("POST", f"/api/v1/actions/workspaces/{ws}/translations/set", body,
                 ctype="application/xml", accept="*/*", raw=True)
            print(f"  {loc} {name}: {done} strings translated" + (f", {missing} missing" if missing else ""))


def clean_translations():
    for ws, name in WORKSPACES.items():
        for loc in LOCALES:
            call("POST", f"/api/v1/actions/workspaces/{ws}/translations/clean", {"locale": loc}, raw=True, **JSON)
        print(f"  {name}: translations removed")


def set_setting(ws, stype, value):
    sid = f"conference_{stype.lower()}"
    path = f"/api/v1/entities/workspaces/{ws}/workspaceSettings"
    existing = {s["attributes"]["type"]: s["id"] for s in call("GET", f"{path}?origin=NATIVE&size=100")["data"]}
    if value is None:
        if stype in existing:
            call("DELETE", f"{path}/{existing[stype]}")
        return
    body = {"data": {"type": "workspaceSetting", "id": existing.get(stype, sid),
                     "attributes": {"type": stype, "content": {"value": value}}}}
    if stype in existing:
        call("PUT", f"{path}/{existing[stype]}", body)
    else:
        call("POST", path, body)


def apply_settings(reset=False):
    for ws, name in WORKSPACES.items():
        loc = None if reset else WORKSPACE_LOCALES.get(ws)
        for stype in SETTING_TYPES:
            set_setting(ws, stype, loc)
        print(f"  {name}: {loc or 'inherit (en-US)'}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", choices=["translations", "settings"])
    ap.add_argument("--reset", action="store_true")
    a = ap.parse_args()
    if a.reset:
        print("Settings:"); apply_settings(reset=True)
        print("Translations:"); clean_translations()
        sys.exit()
    if a.only in (None, "translations"):
        print("Translations:"); push_translations()
    if a.only in (None, "settings"):
        print("Settings:"); apply_settings()
