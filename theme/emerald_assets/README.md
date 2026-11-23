# Emerald theme set: brand assets

Used by `theme/build_themes.py --set=emerald`. emeraldx.com, outdoorretailer.com and cediaexpo.com refuse scripted
downloads, so their logos and photos are kept here and served from the public repo
(`raw.githubusercontent.com/suszterova-sandra/ecommerce-app/main/theme/emerald_assets/...`). The GoodData report does not
render `data:` URIs, so every `logo` must be a remote URL.

| Brand | Workspace | Logo (theme) | Header logo | Background |
|---|---|---|---|---|
| Emerald (parent) | gdc_demo_a7c3afa0… | `emerald_logo.png` (teal, cut from the "Powered by Emerald" footer badge on Emerald show sites) | `emerald_logo_white.png` | nynow.com `DSC07734-scaled.jpg` (show aisle) |
| NY NOW | gdc_demo_c8e457e4… (merchant__bigboxretailer) | nynow.com `NYNOW_Logo_Black_Nav.png` | same (white top bar) | nynow.com `home-00.jpg` |
| Outdoor Retailer | gdc_demo_86a46377… (merchant__clothing) | `or_logo.png` (outdoorretailer.com `OR_Logo_Primary_Icon_black_rgb.png`) | `or_logo_cream.png` (recoloured) | `or_show_floor.jpg` (outdoorretailer.com 2026 email header, resized) |
| CEDIA Expo | gdc_demo_9df6e6ad… (merchant__electronics) | `cedia_expo_logo.png` (cediaexpo.com `CEDIA-EXPO-H-B.png`) | `cedia_expo_logo_white.png` (`CEDIA-EXPO-H-White.png`) | `cedia_expo_panel.jpg` (cediaexpo.com, Jack Goras, resized) |

`emerald_icon.png` (the mark only) is the portal favicon.

Colours: Emerald #025157 / #008098 / #91D500 from emeraldx.com `style.css`; NY NOW #184056 / #9AD0D5 from nynow.com;
Outdoor Retailer olive / cream / yellow sampled from its 2026 campaign banner. CEDIA Expo's site CSS could not be read:
its black wordmark is real, the blue accent (#00A3E0 / #0077C8) is a design choice.

Switch back with `--set=original`, `--set=akitabox` or `--set=franconnect`.
