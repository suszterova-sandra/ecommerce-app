"""Create API tokens for the two demo personas and store them in demo_app/.tokens.json (git-ignored).

    python3 demo_app/setup_tokens.py           # creates missing tokens only
    python3 demo_app/setup_tokens.py --rotate  # delete and recreate

Uses the admin token from ../.env; an org admin may create tokens for other users.
The app needs them so embedded dashboards and AI chat run with each user's own permissions.
"""
import json
import sys
from pathlib import Path

from setup_agents import req

TOKENS = Path(__file__).resolve().parent / ".tokens.json"
USERS = ["sas.analyze.user", "sas.view.user"]
TOKEN_ID = "conference-demo-app"


def main(rotate=False):
    store = json.loads(TOKENS.read_text()) if TOKENS.exists() else {}
    for u in USERS:
        if u in store and not rotate:
            print(u, "token already present")
            continue
        req("DELETE", f"/api/v1/entities/users/{u}/apiTokens/{TOKEN_ID}")
        s, t = req("POST", f"/api/v1/entities/users/{u}/apiTokens",
                   {"data": {"id": TOKEN_ID, "type": "apiToken", "attributes": {}}})
        if s != 201:
            sys.exit(f"{u}: {s} {t[:300]}")
        store[u] = json.loads(t)["data"]["attributes"]["bearerToken"]
        print(u, "token created")
    TOKENS.write_text(json.dumps(store, indent=2))
    TOKENS.chmod(0o600)


if __name__ == "__main__":
    main("--rotate" in sys.argv)
