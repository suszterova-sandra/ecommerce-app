# Open Universities Australia theme set: brand assets

Used by `theme/build_themes.py --set=oua`. Served from the public repo
(`raw.githubusercontent.com/suszterova-sandra/ecommerce-app/main/theme/oua_assets/...`), because the GoodData report
needs remote PNG/JPG logos.

| Brand | Workspace | Logo | Header logo | Background |
|---|---|---|---|---|
| Open Universities Australia (parent) | gdc_demo_a7c3afa0… | `oua_logo.png` (open.edu.au `/images/oua.svg`) | `oua_logo_white.png` (same, white) | `oua_student.jpg` (open.edu.au hero, cropped) |
| Curtin University | gdc_demo_c8e457e4… (merchant__bigboxretailer) | `curtin_logo.png` (open.edu.au `/assets/curtn.svg`) | same (white top bar) | `oua_student.jpg` |
| Griffith University | gdc_demo_86a46377… (merchant__clothing, demo users) | `griffith_logo.png` (`/assets/grf.svg`) | same | `oua_student.jpg` |
| Swinburne University of Technology | gdc_demo_9df6e6ad… (merchant__electronics) | `swinburne_logo.png` (`/assets/swin.svg`) | same | `oua_advisor.jpg` (open.edu.au Open Graph image) |

`oua_icon.png` (open.edu.au `/images/favicon.svg`) is the portal favicon. SVGs were rendered to PNG with headless Chrome.

Colours: OUA blue #3555A6, charcoal #3B3B3C, pink #E42251 and teal #4CBAAC from open.edu.au CSS (font Lato);
university colours from their logo SVGs (Curtin gold #C19609, Griffith red #E51F30, Swinburne red #EC1B2E).

Switch back with `--set=emerald` (also restore the Emerald favicon, title, `#91D500` accent and persona labels in demo_app).
