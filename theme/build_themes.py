"""
Build the conference themes and chart palettes, and optionally deploy them.

    python3 theme/build_themes.py            # write JSON files only
    python3 theme/build_themes.py --deploy   # also PUT/POST to the org and activate them
    python3 theme/build_themes.py conference_nike --deploy   # only one theme
    python3 theme/build_themes.py --set=akitabox --deploy   # switch to the AkitaBox branding

Theme set "original" (default, active):
- conference_dark_lime  -> parent (near-black, lime accent, GoodData visuals)
- conference_ikea       -> child merchant__bigboxretailer (white, IKEA blue and yellow)
- conference_nike       -> child merchant__clothing (white, black, Nike orange)
- conference_samsung    -> child merchant__electronics (white, Samsung blue)

Theme set "akitabox":
- conference_akitabox         -> parent "AkitaBox" (navy #2B3144, gold #F2C318)
- conference_blessing         -> child "Blessing Health System" = merchant__bigboxretailer (navy, blue, green)
- conference_edgewood         -> child "Edgewood College" = merchant__clothing (black, Edgewood red)
- conference_ohio_statehouse  -> child "Ohio Statehouse" = merchant__electronics (navy, gold)

Theme set "franconnect" (python3 theme/build_themes.py --set=franconnect --deploy; also renames the workspaces):
- conference_franconnect     -> parent "FranConnect" (navy #004191, orange #F58220)
- conference_fci             -> child "Floor Coverings International" = merchant__bigboxretailer (navy, red, green)
- conference_paris_baguette  -> child "Paris Baguette" = merchant__clothing (navy #001871, gold #FFC600)
- conference_arbys           -> child "Arby's" = merchant__electronics (Arby's red #DC0032)
The ecommerce data and analytics stay as they are; only names, themes and palettes change.

conference_dark_lime_theme.json is the structural template: every brand theme is derived from it by swapping
colours, so they all stay structurally identical.
The business report takes its colours from documents.colors (backgrounds/texts by id), so the same report
renders in each workspace's brand. GoodData limits a theme to 15,000 characters: the parent's logo is an
inline PNG (the SVG did not render); the brand assets are remote PNG/JPG/SVG URLs. The report (documents) does not
render data: URIs, so a brand "logo" must be a remote URL (it resolves {theme.assets.images.logo} from assets.logos).
"""
import base64
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
AKITABOX = {
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

# Pre-AkitaBox look (the default): Dark Lime parent + IKEA / Nike / Samsung tenant themes.
ORIGINAL = {
    "conference_ikea": {
        "name": "Conference – IKEA (BigBox Retailer)", "ws": BLESSING_WS, "brand": "IKEA",
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
        "name": "Conference – Nike (Clothing)", "ws": EDGEWOOD_WS, "brand": "Nike",
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
        "name": "Conference – Samsung (Electronics)", "ws": OHIO_WS, "brand": "Samsung",
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

def inline_png(name):
    """Small brand PNGs from theme/franconnect_assets, inlined: no public host serves a dark-on-light version."""
    return "data:image/png;base64," + base64.b64encode((HERE / "franconnect_assets" / name).read_bytes()).decode()


# FranConnect (franconnect.com) as the publisher, three of its case-study customers as tenants.
# `ws_name` renames the workspace on --deploy. Logos: theme/franconnect_assets (sources in its README).
FRANCONNECT = {
    "conference_franconnect": {
        "name": "Conference – FranConnect (parent)", "ws": PARENT_WS, "brand": "FranConnect",
        "ws_name": "FranConnect",
        "header": ("#004191", "#FFFFFF", "#F58220"),
        "hex": {"page": "#FFFFFF", "card": "#F4F7FB", "panel": "#E1E8F0", "line": "#DBE4EE", "line2": "#CBD7E4",
                "g5": "#8FA3BC", "g6": "#5E7491", "muted": "#3B4F6B", "g8": "#10213A", "text": "#00152F",
                "subtle": "#6E819A", "accent": "#004191", "accent_hover": "#002E69", "accent_dim": "#F58220"},
        "primary": "#004191",
        "nav": {"bg": "#004191", "border": "#002E69", "item": "#C9D8EC", "selected": "#FFFFFF",
                "selected_bg": "#F58220"},
        "viz": ["#004191", "#F58220", "#3A9AD9", "#00152F", "#FFB066", "#8FB4DE", "#2F9E7A", "#8A9BB0",
                "#B85A0E", "#5C6BC0"],
        "rule": "F58220",
        "kpi_tile": {"bg": "#004191", "border": "#004191", "title": "#C9D8EC", "value": "#FFFFFF",
                     "secondary": "#C9D8EC", "good": "#8FE3C0", "bad": "#FFB3BF"},
        "doc": {"page": "#F4F7FB", "card": "#FFFFFF", "panel": "#E1E8F0"},
        "logo": "https://www.franconnect.com/wp-content/uploads/2020/02/FranConnect-Logo-PRIMARY-Color-Small.png",
        "header_logo": inline_png("franconnect_logo_white.png"),
        "bg": "https://www.franconnect.com/wp-content/uploads/2024/01/shutterstock_2168498267-scaled.jpg",
        "bg_alt": "Franchise owner working on a laptop",
    },
    "conference_fci": {
        "name": "Conference – Floor Coverings International", "ws": BLESSING_WS,  # merchant__bigboxretailer
        "brand": "Floor Coverings International", "ws_name": "Floor Coverings International",
        "header": ("#1C294A", "#FFFFFF", "#80D14A"),
        "hex": {"page": "#FFFFFF", "card": "#FAF9F9", "panel": "#F2EFEC", "line": "#E0E0E0", "line2": "#C9CCD3",
                "g5": "#9097A6", "g6": "#6A7286", "muted": "#35495E", "g8": "#1C294A", "text": "#292929",
                "subtle": "#7E8594", "accent": "#D01F35", "accent_hover": "#A8182A", "accent_dim": "#80D14A"},
        "primary": "#1C294A",
        "nav": {"bg": "#1C294A", "border": "#141E37", "item": "#C7CEDD", "selected": "#1C294A",
                "selected_bg": "#80D14A"},
        "viz": ["#1C294A", "#D01F35", "#80D14A", "#C08726", "#5B7DB1", "#A9B4C8", "#35495E", "#F08A97",
                "#4E8F2A", "#8C7A55"],
        "rule": "D01F35",
        "kpi_tile": {"bg": "#1C294A", "border": "#1C294A", "title": "#C7CEDD", "value": "#FFFFFF",
                     "secondary": "#C7CEDD", "good": "#80D14A", "bad": "#FFB3BF"},
        "doc": {"page": "#D6D0C7", "card": "#FFFFFF", "panel": "#ECE8E2"},  # darker stone report page
        # official transparent logo, hosted on the Eastern Lake County Chamber member page (the report needs a remote URL)
        "logo": "https://chambermaster.blob.core.windows.net/images/customers/527/members/6857/logos/MEMBER_PAGE_HEADER/(Floor_Coverings_Intl_official_Logo_transparent_Back)_FCI_LOGO_RGB_clear_back_1637174394.png",
        "header_logo": "https://floorcoveringsinternational.com/img/upload/fci_logo-white03b25d-1.png",
        "bg": "https://floorcoveringsinternational.com/img/upload/ikjbq92roxtczfnu.webp",
        "bg_alt": "Living room with wide-plank hardwood flooring",
    },
    "conference_paris_baguette": {
        "name": "Conference – Paris Baguette", "ws": EDGEWOOD_WS,  # merchant__clothing
        "brand": "Paris Baguette", "ws_name": "Paris Baguette",
        "header": ("#001871", "#FFFFFF", "#FFC600"),
        "hex": {"page": "#FFFFFF", "card": "#FFFAF3", "panel": "#F3EEE4", "line": "#E6DFD2", "line2": "#CFC6B5",
                "g5": "#9C9584", "g6": "#6E7391", "muted": "#3C4370", "g8": "#0E1144", "text": "#0E1144",
                "subtle": "#7D8299", "accent": "#001871", "accent_hover": "#0E1144", "accent_dim": "#FFC600"},
        "primary": "#001871",
        "nav": {"bg": "#001871", "border": "#0E1144", "item": "#C9CDEB", "selected": "#001871",
                "selected_bg": "#FFC600"},
        "viz": ["#001871", "#FFC600", "#4A6FD1", "#B5835A", "#0E1144", "#9DB0E8", "#2F9E7A", "#E36A5C",
                "#7D8299", "#E8D9B5"],
        "rule": "FFC600",
        "kpi_tile": {"bg": "#001871", "border": "#001871", "title": "#C9CDEB", "value": "#FFC600",
                     "secondary": "#C9CDEB", "good": "#8FE3C0", "bad": "#FFB3BF"},
        "doc": {"page": "#DDD0BB", "card": "#FFFFFF", "panel": "#F0E8DA"},  # darker sand report page
        "logo": "https://upload.wikimedia.org/wikipedia/commons/thumb/b/b7/Paris_Baguette_logo.svg/960px-Paris_Baguette_logo.svg.png",
        "header_logo": "https://parisbaguette.com/wp-content/uploads/2024/04/paris-baguette-logo.svg",
        "bg": "https://parisbaguette.com/wp-content/uploads/2025/01/2024_0910_ParisBaguette_DW9_6560-1536x1024.jpg",
        "bg_alt": "Croissants, fruit danishes and coffee at Paris Baguette",
    },
    "conference_arbys": {
        "name": "Conference – Arby's", "ws": OHIO_WS,  # merchant__electronics
        "brand": "Arby's", "ws_name": "Arby's",
        "header": ("#FFFFFF", "#000000", "#DC0032"),  # white top bar with the red hat logo, like arbys.com
        "hex": {"page": "#FFFFFF", "card": "#FFFBF5", "panel": "#FCF2F2", "line": "#EFE3E3", "line2": "#D9C7C7",
                "g5": "#A39494", "g6": "#737373", "muted": "#4A4040", "g8": "#2B2222", "text": "#000000",
                "subtle": "#8A7F7F", "accent": "#DC0032", "accent_hover": "#B0082B", "accent_dim": "#DC0032"},
        "primary": "#DC0032",
        "nav": {"bg": "#830621", "border": "#5E0418", "item": "#F5CBD3", "selected": "#830621",
                "selected_bg": "#FFFFFF"},
        "viz": ["#DC0032", "#000000", "#F28C28", "#830621", "#737373", "#F5A3B3", "#328500", "#C9A27E",
                "#4A90D9", "#FFC857"],
        "rule": "DC0032",
        "kpi_tile": {"bg": "#DC0032", "border": "#DC0032", "title": "#FCD6DE", "value": "#FFFFFF",
                     "secondary": "#FCD6DE", "good": "#B8F0D8", "bad": "#FFE08A"},
        "doc": {"page": "#FFFBF5", "card": "#FFFFFF", "panel": "#FCF2F2"},
        "logo": "https://upload.wikimedia.org/wikipedia/commons/thumb/f/f4/Arby%27s_logo.svg/960px-Arby%27s_logo.svg.png",
        "bg": "https://images.ctfassets.net/30q5w5l98nbx/3iGaTQDizG4yk5VfEteTjL/8703abaac9a58eb846426821b760d4d2/Website_App_Favorites_2025.jpg",
        "bg_alt": "Arby's roast beef sandwich, gyro, curly fries and shake",
    },
}

SETS = {"original": ORIGINAL, "akitabox": AKITABOX, "franconnect": FRANCONNECT}


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
    which = next((a.split("=", 1)[1] for a in sys.argv[1:] if a.startswith("--set=")), "original")
    tenants = SETS[which]
    jobs = [("conference_dark_lime", "Conference – Dark Lime", parent, PARENT_VIZ, PARENT_WS)] if which == "original" else []
    jobs += [(tid, c["name"], tenant_theme(parent, c), c["viz"], c["ws"]) for tid, c in tenants.items()]
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
            ws_name = tenants.get(tid, {}).get("ws_name")
            if ws_name:
                code, cur = api("GET", f"/api/v1/entities/workspaces/{ws}")
                if code == 200 and cur["data"]["attributes"].get("name") != ws_name:
                    cur["data"]["attributes"]["name"] = ws_name
                    body = {"data": {k: cur["data"][k] for k in ("id", "type", "attributes", "relationships")
                                     if k in cur["data"]}}
                    print("  rename", api("PUT", f"/api/v1/entities/workspaces/{ws}", body)[0], "->", ws_name)


if __name__ == "__main__":
    main()
