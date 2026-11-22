# FranConnect theme set: brand assets

Used by `theme/build_themes.py --set=franconnect`. The GoodData report (documents) does not render `data:` URIs,
so each brand's main `logo` is a public URL. The local PNGs are tight crops used as inline header logos or kept for reference.

| Brand | Workspace | Logo (theme) | Header logo | Background |
|---|---|---|---|---|
| FranConnect (parent) | gdc_demo_a7c3afa0… | franconnect.com `FranConnect-Logo-PRIMARY-Color-Small.png` | `franconnect_logo_white.png` (inline, made from the primary logo) | franconnect.com `shutterstock_2168498267-scaled.jpg` |
| Floor Coverings International | gdc_demo_c8e457e4… (merchant__bigboxretailer) | official transparent PNG on the Eastern Lake County Chamber page | floorcoveringsinternational.com `fci_logo-white03b25d-1.png` | floorcoveringsinternational.com `ikjbq92roxtczfnu.webp` |
| Paris Baguette | gdc_demo_86a46377… (merchant__clothing) | Wikimedia Commons `Paris_Baguette_logo.svg` (PNG render) | parisbaguette.com `paris-baguette-logo.svg` (white) | parisbaguette.com `2024_0910_ParisBaguette_DW9_6560-1536x1024.jpg` |
| Arby's | gdc_demo_9df6e6ad… (merchant__electronics) | Wikimedia Commons `Arby's_logo.svg` (PNG render) | same (white top bar) | arbys.com (Contentful) `Website_App_Favorites_2025.jpg` |

All three tenants are FranConnect case-study customers (franconnect.com/customers/casestudies/).
Switch back with `--set=original` or `--set=akitabox`.
