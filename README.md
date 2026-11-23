# Emerald: conference demo

GoodData Cloud demo on `navy-blue-eagle.trial.cloud.gooddata.com`: one parent workspace (**Emerald**)
with three branded tenants, all Emerald trade shows (**NY NOW**, **Outdoor Retailer**, **CEDIA Expo**), on unchanged
ecommerce data, and a React portal
that switches between an admin, an Analyze user and a View user with their real permissions.

| Folder | What it is |
|---|---|
| `demo_app/` | The portal: Vite + React UI and a small Python backend. Run steps in [demo_app/README.md](demo_app/README.md). |
| `analytics/` | Analytics as code of the parent workspace (`gooddata.yaml` profile). |
| `theme/` | Branded themes and chart palettes per workspace (`build_themes.py --set=emerald --deploy`; also `original`, `akitabox`, `franconnect`). |
| `publisher/` | The AI business report document and its builder. |
| `localization/` | Metadata translations (de-DE, fr-FR). |
| `customer_data/` + `*.ipynb` | Tenant provisioning demo: 2 new child workspaces with WDFs, groups, users, UDFs and permissions. |

## Credentials

- `demo_app/.tokens.json`: API tokens of `sas.analyze.user` and `sas.view.user`. They are committed on purpose,
  so the user switcher works after a clone. Keep this repository private.
- The admin token is **not** committed. Copy `.env.example` to `.env` and set `GOODDATA_API_TOKEN` (the backend
  needs it for the admin view and the Control Center).

To revoke and recreate the user tokens: `python3 demo_app/setup_tokens.py --rotate` (needs the admin `.env`).

## Tenant provisioning notebooks

Three notebooks provision the same input (`customer_data/*.csv`) under the parent workspace, run from this folder
with the admin `.env`:

| Notebook | How |
|---|---|
| `user_provisioning_flow.ipynb` | GoodData Python SDK, one step after another (the readable version) |
| `scalability.ipynb` | Python SDK, the same calls in 4 parallel dependency waves + a scaling projection |
| `api_provisioning.ipynb` | Plain REST API (`requests`), parallel waves, per-endpoint call log, optional teardown |

They create `conf_furniture_outlet` (merchant__bigboxretailer; Furniture, Home Goods) and `conf_audio_store`
(merchant__electronics; Audio & Video Accessories), each with values for both workspace data filters
(`WDF__CLIENT_ID`, `WDF__PRODUCT_CATEGORY`), a Managers and a Viewers group, and 5 dummy `@example.com` users
in total, 3 of them with a user data filter on `customer_state`. All calls are idempotent, so re-runs update in place.
The trial org is at its user limit: new rows in `customer_users.csv` fail with "Reached plan limits" unless users are removed first.
