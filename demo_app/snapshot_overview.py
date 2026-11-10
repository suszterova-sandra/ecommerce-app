"""Write web/public/overview.json: the admin overview (workspaces, themes, data filters, groups, agents) that the
static GitHub Pages build shows to visitors who are not signed in as an admin. Re-run after changing themes,
workspaces or agents, then commit:

    python3 demo_app/snapshot_overview.py

Uses the admin token from ../.env; the token itself is not written anywhere.
"""
import json
from pathlib import Path

import server

out = Path(__file__).resolve().parent / "web" / "public" / "overview.json"
out.parent.mkdir(parents=True, exist_ok=True)
data = server._build_overview()
out.write_text(json.dumps(data, indent=1))
print(f"wrote {out} ({len(data['workspaces'])} workspaces, {len(data['themes'])} themes)")
