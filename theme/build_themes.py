"""
Build the conference themes and chart palettes, and optionally deploy them.

    python3 theme/build_themes.py            # write JSON files only
    python3 theme/build_themes.py --deploy   # also PUT/POST to the org and activate them
    python3 theme/build_themes.py conference_nike --deploy   # only one theme

- conference_dark_lime  -> parent workspace "Ecommerce Company" (near-black, lime accent, GoodData visuals)
- conference_ikea       -> child "Customer A (S)" = merchant__bigboxretailer (white, IKEA blue and yellow)
- conference_nike       -> child "Customer B (S)" = merchant__clothing (white, black, Nike orange)
- conference_samsung    -> child "Customer C (S)" = merchant__electronics (white, Samsung blue)

The IKEA theme is derived from the parent theme by swapping colours, so both stay structurally identical.
The business report takes its colours from documents.colors (backgrounds/texts by id), so the same report
renders in each workspace's brand. GoodData limits a theme to 15,000 characters: the parent's logo is an
inline PNG (the SVG did not render); the IKEA assets are remote PNG/JPG URLs.
"""
import json
import os
import sys
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
HOST = "https://navy-blue-eagle.trial.cloud.gooddata.com"
PARENT_WS = "gdc_demo_a7c3afa0-ca91-40db-a3a8-df4d5044e92f"
IKEA_WS = "gdc_demo_c8e457e4-64e9-4226-b2d7-b914e5f260b5"   # Customer A (S) = merchant__bigboxretailer
CLOTHING_WS = "gdc_demo_86a46377-cad8-4c3d-ab7c-6ba753b49b2c"  # Customer B (S) = merchant__clothing
ELECTRONICS_WS = "gdc_demo_9df6e6ad-de8a-42e3-9893-f13abe01e203"  # Customer C (S) = merchant__electronics

# Colour roles read by the report via {theme.colors.backgrounds.<id>} / {theme.colors.texts.<id>}
DOC_BG_IDS = ["page", "card", "panel", "accent"]
DOC_TEXT_IDS = ["default", "muted", "subtle", "accent", "inverse"]

PARENT_HEX = {  # role -> parent colour
    "page": "#0B0D10", "card": "#14171C", "panel": "#1B1F25", "line": "#252A31", "line2": "#343A43",
    "g5": "#4E5560", "g6": "#747C88", "muted": "#9BA3AE", "g8": "#C9CED6", "text": "#F2F4F7",
    "subtle": "#5B636E", "accent": "#D4F24A", "accent_hover": "#C3E635", "accent_dim": "#2A3312",
}
PARENT_VIZ = ["#3DD6C4", "#6C8CFF", "#A98BFA", "#F5C451", "#3FA9E0", "#F27A9B", "#E4E7EC", "#2A9D8F",
              "#8A94A3", "#F4A27A"]

# Light tenant themes, derived from the parent by colour role. `primary` = buttons/links (defaults to accent),
# `accent` = report kickers/numbers and highlights, `accent_dim` = selected navigation item background.
TENANTS = {
    "conference_ikea": {
        "name": "Conference – IKEA (BigBox Retailer)", "ws": IKEA_WS, "brand": "IKEA",
        "header": ("#0058A3", "#FFFFFF", "#FFDB00"),  # top bar: background, text, active item
        "hex": {"page": "#FFFFFF", "card": "#F4F7FB", "panel": "#E8F0F9", "line": "#D6E2EF", "line2": "#B8CCE3",
                "g5": "#8AA4C2", "g6": "#5F7FA3", "muted": "#3D5A7A", "g8": "#1F3A5C", "text": "#0B1F33",
                "subtle": "#6B8299", "accent": "#0058A3", "accent_hover": "#004A8C", "accent_dim": "#FFDB00"},
        "primary": "#0058A3",
        "nav": {"bg": "#0058A3", "border": "#004A8C", "item": "#D6E6F7", "selected": "#0B1F33",
                "selected_bg": "#FFDB00"},
        "viz": ["#0058A3", "#FFDB00", "#4A9BE0", "#0B2F55", "#F2A900", "#8DBBE8", "#2F9E7A", "#E36A5C",
                "#7A8FA6", "#C9A400"],
        "rule": "FFDB00",
        # dashboard KPI tiles: IKEA blue tile, yellow main value
        "kpi_tile": {"bg": "#0058A3", "border": "#0058A3", "title": "#FFFFFF", "value": "#FFDB00",
                     "secondary": "#D6E6F7", "good": "#8FE3C0", "bad": "#FFB3BF"},
        # report: light neutral-grey pages, white cards
        "doc": {"page": "#F4F5F7", "card": "#FFFFFF", "panel": "#EAEDF1"},
        "logo": "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c5/Ikea_logo.svg/1280px-Ikea_logo.svg.png",
        "bg": "https://cc.cz/wp-content/uploads/2017/01/ikea.jpg", "bg_alt": "IKEA store at dusk",
    },
    "conference_nike": {
        "name": "Conference – Nike (Clothing)", "ws": CLOTHING_WS, "brand": "Nike",
        "header": ("#111111", "#FFFFFF", "#FA5400"),  # top bar: background, text, active item
        "hex": {"page": "#FFFFFF", "card": "#F5F5F5", "panel": "#EFEFEF", "line": "#E2E2E2", "line2": "#CCCCCC",
                "g5": "#9E9E9E", "g6": "#757575", "muted": "#4D4D4D", "g8": "#2B2B2B", "text": "#111111",
                "subtle": "#8A8A8A", "accent": "#FA5400", "accent_hover": "#E04B00", "accent_dim": "#FA5400"},
        "primary": "#111111",
        "nav": {"bg": "#111111", "border": "#2B2B2B", "item": "#BDBDBD", "selected": "#FFFFFF",
                "selected_bg": "#FA5400"},
        "viz": ["#111111", "#FA5400", "#8A8A8A", "#FF9A5C", "#3A3A3A", "#CFCFCF", "#2F9E7A", "#4A90D9",
                "#B23A00", "#5E5E5E"],
        "rule": "FA5400",
        # report: light grey pages, white cards (charts keep their white plot area)
        "doc": {"page": "#ECECEC", "card": "#FFFFFF", "panel": "#F7F7F7"},
        "logo": "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a6/Logo_NIKE.svg/1280px-Logo_NIKE.svg.png",
        "bg": "https://www.weavabel.com/hubfs/thomas-serer-R_0rTS9ENnk-unsplash.jpeg",
        "bg_alt": "Nike store front at night",
    },
    "conference_samsung": {
        "name": "Conference – Samsung (Electronics)", "ws": ELECTRONICS_WS, "brand": "Samsung",
        "header": ("#1428A0", "#FFFFFF", "#8FD3FF"),  # top bar: background, text, active item
        "hex": {"page": "#FFFFFF", "card": "#F5F6F8", "panel": "#ECEEF3", "line": "#DDE1EA", "line2": "#C3C9D6",
                "g5": "#98A1B3", "g6": "#6B7487", "muted": "#474F60", "g8": "#262B36", "text": "#0B0B0B",
                "subtle": "#7C8496", "accent": "#1428A0", "accent_hover": "#0F1F80", "accent_dim": "#FFFFFF"},
        "primary": "#1428A0",
        "nav": {"bg": "#1428A0", "border": "#0F1F80", "item": "#C9D1F5", "selected": "#1428A0",
                "selected_bg": "#FFFFFF"},
        "viz": ["#1428A0", "#00A3E0", "#6C7BD8", "#0B0B0B", "#8A94A6", "#B3C2FF", "#2F9E7A", "#F2A900",
                "#E36A5C", "#4A5BC4"],
        "rule": "1428A0",
        # dashboard KPI tiles: Samsung blue tile, white value
        "kpi_tile": {"bg": "#1428A0", "border": "#1428A0", "title": "#C9D1F5", "value": "#FFFFFF",
                     "secondary": "#C9D1F5", "good": "#8FE3C0", "bad": "#FFB3BF"},
        # report: light grey pages, white cards
        "doc": {"page": "#EFF1F5", "card": "#FFFFFF", "panel": "#F7F8FA"},
        "logo": "https://upload.wikimedia.org/wikipedia/commons/0/00/Samsung_Orig_Wordmark_BLACK_RGB.png",
        "bg": "https://vivaldigroup.com/wp-content/uploads/2022/06/case_study-header-Samsung-large.jpg",
        "bg_alt": "Samsung store display with Galaxy phones",
    },
}


def doc_colors(hexes):
    return {
        "backgrounds": [{"id": "page", "color": hexes["page"]}, {"id": "card", "color": hexes["card"]},
                        {"id": "panel", "color": hexes["panel"]}, {"id": "accent", "color": hexes["accent"]}],
        "texts": [{"id": "default", "color": hexes["text"]}, {"id": "muted", "color": hexes["muted"]},
                  {"id": "subtle", "color": hexes["subtle"]}, {"id": "accent", "color": hexes["accent"]},
                  {"id": "inverse", "color": hexes["page"]}],
    }


def recolor(obj, mapping):
    s = json.dumps(obj)
    for old, new in mapping.items():
        s = s.replace(old, new).replace(old.lower(), new)
    return json.loads(s)


def parent_theme():
    t = json.load(open(HERE / "conference_dark_lime_theme.json"))
    t["documents"]["colors"] = doc_colors(PARENT_HEX)
    t["documents"]["visualizationPalette"] = PARENT_VIZ
    t["header"] = {"backgroundColor": "#101317", "color": "#9BA3AE", "activeColor": "#D4F24A"}  # top app bar
    return t


def tenant_theme(parent, cfg):
    hexes, nav = cfg["hex"], cfg["nav"]
    t = recolor({k: v for k, v in parent.items() if k not in ("assets", "images")},
                {PARENT_HEX[k]: hexes[k] for k in PARENT_HEX})
    good, bad = "#2F9E7A", "#D1435B"
    t["palette"]["primary"] = {"base": cfg["primary"], "contrast": "#FFFFFF"}
    t["palette"]["error"]["base"], t["palette"]["success"]["base"] = bad, good
    t["kpi"]["value"] = {"positiveColor": good, "negativeColor": bad}
    t["dashboards"]["content"]["kpiWidget"]["kpi"]["value"] = {"positiveColor": good, "negativeColor": bad}
    t["modal"]["outsideBackgroundColor"] = "rgba(0, 0, 0, 0.45)"
    t["dashboards"]["navigation"] = {"title": {"color": "#FFFFFF"}, "backgroundColor": nav["bg"],
                                     "borderColor": nav["border"],
                                     "item": {"color": nav["item"], "hoverColor": "#FFFFFF",
                                              "selectedColor": nav["selected"],
                                              "selectedBackgroundColor": nav["selected_bg"]}}
    for w in ("widget", "kpiWidget"):  # white cards with a soft border on a lightly tinted page
        t["dashboards"]["content"][w].update(backgroundColor="#FFFFFF", borderColor=hexes["line"])
    t["dashboards"]["content"]["backgroundColor"] = hexes["card"]
    t["dashboards"]["filterBar"]["backgroundColor"] = "#FFFFFF"
    t["chart"]["backgroundColor"] = "#FFFFFF"
    t["tooltip"] = {"color": "#FFFFFF", "backgroundColor": hexes["text"]}
    t["chart"].update(tooltipBackgroundColor=hexes["text"], tooltipBorderColor=hexes["text"],
                      tooltipLabelColor=hexes["line2"], tooltipValueColor="#FFFFFF")
    if "kpi_tile" in cfg:
        k = cfg["kpi_tile"]
        tile = t["dashboards"]["content"]["kpiWidget"]
        tile.update(backgroundColor=k["bg"], borderColor=k["border"])
        tile["title"]["color"] = k["title"]
        tile["kpi"] = {"primaryMeasureColor": k["value"], "secondaryInfoColor": k["secondary"],
                       "value": {"positiveColor": k["good"], "negativeColor": k["bad"]}}
    doc_hex = {**hexes, **cfg.get("doc", {})}
    t["documents"]["colors"] = doc_colors(doc_hex)
    t["documents"]["page"] = {"backgroundColor": doc_hex["page"]}
    t["documents"]["visualizationPalette"] = cfg["viz"]
    spacer = next(a for a in parent["assets"]["images"] if a["id"] == "spacer")
    img = lambda i, u, ti, alt: {"id": i, "url": u, "title": ti, "altText": alt}
    logo = img("logo", cfg["logo"], f"{cfg['brand']} logo", f"{cfg['brand']} logo")
    bgs = [img("cover_bg", cfg["bg"], "Cover background", cfg["bg_alt"]),
           img("section_bg", cfg["bg"], "Section background", cfg["bg_alt"])]
    rule = img("accent_bar", f"https://placehold.co/1600x12/{cfg['rule']}/{cfg['rule']}/png", "Accent rule",
               "Accent rule")
    t["assets"] = {"logos": [logo], "backgrounds": bgs, "images": bgs + [rule, logo, spacer]}
    t["images"] = {"logo": f"url({cfg['logo']})"}
    h = cfg["header"]
    t["header"] = {"backgroundColor": h[0], "color": h[1], "activeColor": h[2]}  # top app bar
    return t


def palette(viz):
    h = lambda x: {"r": int(x[1:3], 16), "g": int(x[3:5], 16), "b": int(x[5:7], 16)}
    return {"colorPalette": [{"guid": f"{i + 1:02d}", "fill": h(c)} for i, c in enumerate(viz)]}


def api(method, path, body=None):
    req = urllib.request.Request(HOST + path, method=method, data=json.dumps(body).encode() if body else None,
                                 headers={"Authorization": f"Bearer {os.environ['GOODDATA_API_TOKEN']}",
                                          "Content-Type": "application/vnd.gooddata.api+json"})
    try:
        with urllib.request.urlopen(req) as r:
            return r.status, json.loads(r.read() or b"null")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()[:300]


def upsert(kind, oid, name, content):
    body = {"data": {"id": oid, "type": kind[:-1], "attributes": {"name": name, "content": content}}}
    code, _ = api("PUT", f"/api/v1/entities/{kind}/{oid}", body)
    if code == 404:
        code, _ = api("POST", f"/api/v1/entities/{kind}", body)
    return code


def activate(ws, setting_type, ref):
    code, res = api("GET", f"/api/v1/entities/workspaces/{ws}/workspaceSettings?origin=NATIVE")
    existing = next((s for s in res["data"] if s["attributes"]["type"] == setting_type), None) if code == 200 else None
    sid = existing["id"] if existing else f"{setting_type.lower()}_conference"
    body = {"data": {"id": sid, "type": "workspaceSetting",
                     "attributes": {"type": setting_type, "content": ref}}}
    if existing:
        return api("PUT", f"/api/v1/entities/workspaces/{ws}/workspaceSettings/{sid}", body)[0]
    return api("POST", f"/api/v1/entities/workspaces/{ws}/workspaceSettings", body)[0]


def main():
    parent = parent_theme()
    jobs = [("conference_dark_lime", "Conference – Dark Lime", parent, PARENT_VIZ, PARENT_WS)]
    jobs += [(tid, c["name"], tenant_theme(parent, c), c["viz"], c["ws"]) for tid, c in TENANTS.items()]
    only = [a for a in sys.argv[1:] if not a.startswith("--")]
    for tid, name, theme, viz, ws in jobs:
        if only and tid not in only:
            continue
        size = len(json.dumps(theme))
        assert size < 15000, f"{tid} is {size} chars (limit 15000)"
        (HERE / f"{tid}_theme.json").write_text(json.dumps(theme, indent=2) + "\n")
        (HERE / f"{tid}_palette.json").write_text(json.dumps(palette(viz), indent=2) + "\n")
        print(f"wrote {tid}_theme.json ({size} chars) and {tid}_palette.json")
        if "--deploy" in sys.argv:
            print("  theme", upsert("themes", tid, name, theme),
                  "| palette", upsert("colorPalettes", tid, name, palette(viz)),
                  "| ACTIVE_THEME", activate(ws, "ACTIVE_THEME", {"id": tid, "type": "theme"}),
                  "| ACTIVE_COLOR_PALETTE", activate(ws, "ACTIVE_COLOR_PALETTE", {"id": tid, "type": "colorPalette"}),
                  f"-> {ws}")


if __name__ == "__main__":
    main()
