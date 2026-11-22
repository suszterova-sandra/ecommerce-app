# FranConnect: conference demo

GoodData Cloud demo on `navy-blue-eagle.trial.cloud.gooddata.com`: one parent workspace (**FranConnect**)
with three branded tenants, all FranConnect case-study customers (**Floor Coverings International**, **Paris Baguette**,
**Arby's**), on unchanged ecommerce data, and a React portal
that switches between an admin, an Analyze user and a View user with their real permissions.

| Folder | What it is |
|---|---|
| `demo_app/` | The portal: Vite + React UI and a small Python backend. Run steps in [demo_app/README.md](demo_app/README.md). |
| `analytics/` | Analytics as code of the parent workspace (`gooddata.yaml` profile). |
| `theme/` | Branded themes and chart palettes per workspace (`build_themes.py --set=franconnect --deploy`; also `original`, `akitabox`). |
| `publisher/` | The AI business report document and its builder. |
| `localization/` | Metadata translations (de-DE, fr-FR). |

## Credentials

- `demo_app/.tokens.json`: API tokens of `sas.analyze.user` and `sas.view.user`. They are committed on purpose,
  so the user switcher works after a clone. Keep this repository private.
- The admin token is **not** committed. Copy `.env.example` to `.env` and set `GOODDATA_API_TOKEN` (the backend
  needs it for the admin view and the Control Center).

To revoke and recreate the user tokens: `python3 demo_app/setup_tokens.py --rotate` (needs the admin `.env`).
