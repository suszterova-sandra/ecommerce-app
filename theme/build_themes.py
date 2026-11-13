"""
Build the conference themes and chart palettes, and optionally deploy them.

    python3 theme/build_themes.py            # write JSON files only
    python3 theme/build_themes.py --deploy   # also PUT/POST to the org and activate them
    python3 theme/build_themes.py conference_edgewood --deploy   # only one theme

- conference_akitabox         -> parent "AkitaBox" (navy #2B3144, gold #F2C318)
- conference_blessing         -> child "Blessing Health System" = merchant__bigboxretailer (navy, blue, green)
- conference_edgewood         -> child "Edgewood College" = merchant__clothing (black, Edgewood red)
- conference_ohio_statehouse  -> child "Ohio Statehouse" = merchant__electronics (navy, gold)

conference_dark_lime_theme.json is the structural template: every brand theme is derived from it by swapping
colours, so they all stay structurally identical.
The business report takes its colours from documents.colors (backgrounds/texts by id), so the same report
renders in each workspace's brand. GoodData limits a theme to 15,000 characters: the parent's logo is an
inline PNG (the SVG did not render); the brand assets are remote PNG/JPG/SVG URLs.
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
BLESSING_WS = "gdc_demo_c8e457e4-64e9-4226-b2d7-b914e5f260b5"  # Blessing Health System = merchant__bigboxretailer
EDGEWOOD_WS = "gdc_demo_86a46377-cad8-4c3d-ab7c-6ba753b49b2c"  # Edgewood College = merchant__clothing
OHIO_WS = "gdc_demo_9df6e6ad-de8a-42e3-9893-f13abe01e203"      # Ohio Statehouse = merchant__electronics



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

# Light brand themes, derived from the parent template by colour role. `primary` = buttons/links,
# `accent` = report kickers/numbers and highlights, `accent_dim` = selected navigation item background.
# `logo` sits on white tiles (demo app, reports); `header_logo` (optional) is the variant for a dark top bar.
TENANTS = {
    "conference_akitabox": {
        "name": "Conference – AkitaBox (parent)", "ws": PARENT_WS, "brand": "AkitaBox",
        "header": ("#2B3144", "#FFFFFF", "#F2C318"),  # top bar: background, text, active item
        "hex": {"page": "#FFFFFF", "card": "#F5F6F8", "panel": "#EFF0F2", "line": "#DFE2E8", "line2": "#C4C9D4",
                "g5": "#959CAD", "g6": "#6B7287", "muted": "#4A5165", "g8": "#2B3144", "text": "#1A1E2B",
                "subtle": "#7D8497", "accent": "#2B3144", "accent_hover": "#1F2433", "accent_dim": "#F2C318"},
        "primary": "#2B3144",
        "nav": {"bg": "#2B3144", "border": "#1F2433", "item": "#C4C9D4", "selected": "#2B3144",
                "selected_bg": "#F2C318"},
        "viz": ["#2B3144", "#F2C318", "#1E90FF", "#CA982C", "#6B7287", "#8ED1FC", "#2F9E7A", "#E36A5C",
                "#8A6B2A", "#AEB4C2"],
        "rule": "F2C318",
        "kpi_tile": {"bg": "#2B3144", "border": "#2B3144", "title": "#C4C9D4", "value": "#F2C318",
                     "secondary": "#C4C9D4", "good": "#8FE3C0", "bad": "#FFB3BF"},
        "doc": {"page": "#EFF0F2", "card": "#FFFFFF", "panel": "#F7F8FA"},
        "logo": "https://builtworlds.com/wp-content/uploads/2021/12/AkitaBox-Logos-Horizontal_Full-Color-RGB-784x392.png",
        "header_logo": "https://home.akitabox.com/wp-content/uploads/2022/02/ab-logo-light.svg",
        "bg": "https://home.akitabox.com/wp-content/uploads/2023/01/AkitaBox-FCA-for-O_O-FCA-Page-Sub-Image-1.jpg",
        "bg_alt": "AkitaBox facility condition assessment",
    },
    "conference_blessing": {
        "name": "Conference – Blessing Health System", "ws": BLESSING_WS, "brand": "Blessing Health System",
        "header": ("#FFFFFF", "#00316B", "#0064A5"),  # white top bar like blessinghealth.org
        "hex": {"page": "#FFFFFF", "card": "#F5F7FA", "panel": "#E8EFF7", "line": "#D7E1EC", "line2": "#B9C8DA",
                "g5": "#8BA0B9", "g6": "#5E7893", "muted": "#3A3A3A", "g8": "#012248", "text": "#012248",
                "subtle": "#878787", "accent": "#0064A5", "accent_hover": "#00316B", "accent_dim": "#A6CF39"},
        "primary": "#0064A5",
        "nav": {"bg": "#00316B", "border": "#012248", "item": "#C5D6EA", "selected": "#00316B",
                "selected_bg": "#A6CF39"},
        "viz": ["#00316B", "#0064A5", "#2098D1", "#A6CF39", "#CF6611", "#87B60B", "#7FB8E0", "#878787",
                "#012248", "#F2B27A"],
        "rule": "A6CF39",
        "kpi_tile": {"bg": "#00316B", "border": "#00316B", "title": "#C5D6EA", "value": "#FFFFFF",
                     "secondary": "#C5D6EA", "good": "#A6CF39", "bad": "#FFB3BF"},
        "doc": {"page": "#F5F5F5", "card": "#FFFFFF", "panel": "#E8EFF7"},
        "logo": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcS8_-SvllqZODZN6uvnhyEMPH0EMbW-aSWyBDvbg5N4ig&s=10",
        "bg": "https://www.siumed.edu/sites/default/files/u2261/southview.jpg",
        "bg_alt": "Blessing Hospital campus",
    },
    "conference_edgewood": {
        "name": "Conference – Edgewood College", "ws": EDGEWOOD_WS, "brand": "Edgewood College",
        "header": ("#1C1C1C", "#FFFFFF", "#FF4A4A"),
        "hex": {"page": "#FFFFFF", "card": "#F6F5F5", "panel": "#EFEDED", "line": "#E2DFDF", "line2": "#CCC7C7",
                "g5": "#9E9898", "g6": "#757070", "muted": "#4A4646", "g8": "#32373C", "text": "#1C1C1C",
                "subtle": "#8A8585", "accent": "#BB0000", "accent_hover": "#990000", "accent_dim": "#BB0000"},
        "primary": "#BB0000",
        "nav": {"bg": "#1C1C1C", "border": "#32373C", "item": "#C9C5C5", "selected": "#FFFFFF",
                "selected_bg": "#BB0000"},
        "viz": ["#BB0000", "#1C1C1C", "#8A8585", "#E36A5C", "#5E1010", "#D9B8B8", "#2F9E7A", "#4A90D9",
                "#F2A900", "#32373C"],
        "rule": "BB0000",
        "kpi_tile": {"bg": "#BB0000", "border": "#BB0000", "title": "#FBD9D9", "value": "#FFFFFF",
                     "secondary": "#FBD9D9", "good": "#B8F0D8", "bad": "#FFE08A"},
        "doc": {"page": "#EFEDED", "card": "#FFFFFF", "panel": "#F7F6F6"},
        "logo": "https://www.edgewood.edu/wp-content/uploads/edgewood-university-logo.svg",
        "header_logo": "https://www.edgewood.edu/wp-content/uploads/edgewood-university-logo-reverse.svg",
        "bg": "https://www.commonapp.org/static/f9c430a914f85c6af11f98776eda22c3/edgewood-university_768.jpg",
        "bg_alt": "Edgewood campus",
    },
    "conference_ohio_statehouse": {
        "name": "Conference – Ohio Statehouse", "ws": OHIO_WS, "brand": "Ohio Statehouse",
        "header": ("#1B365D", "#FFFFFF", "#D4A62A"),
        "hex": {"page": "#FFFFFF", "card": "#F6F5F1", "panel": "#EEEBE2", "line": "#DEDAD0", "line2": "#C6C0B1",
                "g5": "#9A9686", "g6": "#6F7A8C", "muted": "#475468", "g8": "#1B365D", "text": "#0F1E33",
                "subtle": "#7A8496", "accent": "#1B365D", "accent_hover": "#12274A", "accent_dim": "#D4A62A"},
        "primary": "#1B365D",
        "nav": {"bg": "#1B365D", "border": "#12274A", "item": "#C8D3E3", "selected": "#1B365D",
                "selected_bg": "#D4A62A"},
        "viz": ["#1B365D", "#D4A62A", "#A6192E", "#5B7DB1", "#8C7A55", "#B8C7DD", "#2F9E7A", "#E8CF8A",
                "#6F7A8C", "#D97A6C"],
        "rule": "D4A62A",
        "kpi_tile": {"bg": "#1B365D", "border": "#1B365D", "title": "#C8D3E3", "value": "#D4A62A",
                     "secondary": "#C8D3E3", "good": "#8FE3C0", "bad": "#FFB3BF"},
        "doc": {"page": "#F6F5F1", "card": "#FFFFFF", "panel": "#EEEBE2"},
        "logo": "https://upload.wikimedia.org/wikipedia/commons/thumb/f/f3/Seal_of_Ohio.svg/500px-Seal_of_Ohio.svg.png",
        "bg": "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a6/Ohio_Statehouse_exterior.jpg/1920px-Ohio_Statehouse_exterior.jpg",
        "bg_alt": "Ohio Statehouse exterior",
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
    t["images"] = {"logo": f"url({cfg.get('header_logo', cfg['logo'])})"}
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
    jobs = [(tid, c["name"], tenant_theme(parent, c), c["viz"], c["ws"]) for tid, c in TENANTS.items()]
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
