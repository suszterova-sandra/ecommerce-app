"""Conference demo app: localhost shell around the Ecommerce (Conference) workspaces.

    python3 demo_app/server.py            # backend on :8765
    cd demo_app/web && npm run dev        # React UI on http://localhost:5173 (proxies /gd and /app here)

- /gd/<path>        proxy to GoodData, authenticated as the persona in the X-Persona header,
                    so every list, permission check and AI chat runs with that user's own access.
- /app/personas     who can be impersonated (admin from ../.env, users from .tokens.json)
- /app/token        token handed to embedded iframes via the setApiToken postMessage handshake
- /app/overview     admin-only facts for the Control Center (hierarchy, themes, WDFs, access, agents)

Binds to 127.0.0.1 only: the tokens it hands out are real.
"""
import json
import mimetypes
import sys
import threading
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from http.client import HTTPSConnection
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
STATIC = HERE / "web" / "dist"  # React build (npm run build); in dev, Vite serves the UI on :5173
HOST = "navy-blue-eagle.trial.cloud.gooddata.com"
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8765
PARENT_WS = "gdc_demo_a7c3afa0-ca91-40db-a3a8-df4d5044e92f"
REPORT_ID = "ecommerce_business_report"


def _env():
    env = {}
    for line in (ROOT / ".env").read_text().splitlines():
        if "=" in line and not line.lstrip().startswith("#"):
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip().strip('"').strip("'")
    return env


ADMIN_TOKEN = _env()["GOODDATA_API_TOKEN"]

PERSONAS = [
    {"id": "admin", "userId": "sandra.suszterova", "name": "Sandra Suszterova", "initials": "SS",
     "role": "Organization admin", "tagline": "Manages the parent workspace, tenants, themes and AI agents"},
    {"id": "analyze", "userId": "sas.analyze.user", "name": "Analyze User", "initials": "AU",
     "role": "Analyst · Fashion Store", "tagline": "Explores data, builds visualizations and metrics"},
    {"id": "view", "userId": "sas.view.user", "name": "View User", "initials": "VU",
     "role": "Viewer · Fashion Store", "tagline": "Consumes dashboards, reports and AI summaries"},
]


def token_for(persona):
    if persona == "admin":
        return ADMIN_TOKEN
    p = next((p for p in PERSONAS if p["id"] == persona), None)
    f = HERE / ".tokens.json"
    if not p or not f.exists():
        return None
    return json.loads(f.read_text()).get(p["userId"])


def gd(path, token=ADMIN_TOKEN):
    r = urllib.request.Request(f"https://{HOST}{path}", headers={"Authorization": f"Bearer {token}"})
    with urllib.request.urlopen(r, timeout=30) as x:
        return json.loads(x.read().decode())


_cache = {}
_cache_lock = threading.Lock()
TTL = 300  # seconds before the overview is refreshed in the background


def _build_overview():
    """Admin view of the conference tree. All GoodData calls run in parallel."""
    with ThreadPoolExecutor(12) as ex:
        f_ws = ex.submit(gd, "/api/v1/entities/workspaces?include=parent&size=500")
        f_wdf = ex.submit(gd, "/api/v1/layout/workspaceDataFilters")
        f_groups = ex.submit(gd, "/api/v1/entities/userGroups?size=200")
        f_agents = ex.submit(gd, "/api/v1/entities/agents?include=userGroups&size=200")
        f_users = {p["id"]: ex.submit(gd, f"/api/v1/entities/users/{p['userId']}?include=userGroups") for p in PERSONAS}

        tree = [w for w in f_ws.result()["data"] if w["id"] == PARENT_WS or
                ((w.get("relationships") or {}).get("parent") or {}).get("data", {}).get("id") == PARENT_WS]
        calls = {}
        for w in tree:
            wid = w["id"]
            calls[wid] = (ex.submit(gd, f"/api/v1/entities/workspaces/{wid}/workspaceSettings?origin=NATIVE"),
                          ex.submit(gd, f"/api/v1/layout/workspaces/{wid}/permissions"),
                          ex.submit(gd, f"/api/v1/entities/workspaces/{wid}/analyticalDashboards?size=100&origin=ALL"))
        details = []
        for w in tree:
            settings, perms, dashboards = (f.result() for f in calls[w["id"]])
            theme_id = next((x["attributes"]["content"]["id"] for x in settings["data"]
                             if x["attributes"]["type"] == "ACTIVE_THEME"), None)
            details.append({"id": w["id"], "name": w["attributes"]["name"].strip(), "isParent": w["id"] == PARENT_WS,
                            "themeId": theme_id, "permissions": perms.get("permissions", []),
                            "hierarchyPermissions": perms.get("hierarchyPermissions", []),
                            "dashboards": [{"id": d["id"], "title": d["attributes"]["title"]} for d in dashboards["data"]]})

        theme_calls = {tid: ex.submit(gd, f"/api/v1/entities/themes/{tid}") for tid in {d["themeId"] for d in details if d["themeId"]}}
        themes = {}
        for tid, f in theme_calls.items():
            c = f.result()["data"]["attributes"]
            content = c["content"]
            assets = content.get("assets", {})
            logo = next((l["url"] for l in assets.get("logos", []) if l.get("id") == "logo"), None)
            cover = next((b["url"] for b in assets.get("backgrounds", []) if b.get("id") == "cover_bg"), None)
            themes[tid] = {"id": tid, "name": c.get("name", tid), "palette": content.get("palette", {}), "logo": logo, "cover": cover,
                           "accent": (content.get("header") or {}).get("activeColor")}

        wdfs = [{"id": f["id"], "title": f["title"], "column": f["columnName"],
                 "values": {x["workspace"]["id"]: x["filterValues"] for x in f["workspaceDataFilterSettings"]}}
                for f in f_wdf.result()["workspaceDataFilters"] if f.get("workspace", {}).get("id") == PARENT_WS]
        groups = {g["id"]: g["attributes"].get("name", g["id"]) for g in f_groups.result()["data"]}
        members = {pid: [g["id"] for g in f.result()["data"].get("relationships", {}).get("userGroups", {}).get("data", [])]
                   for pid, f in f_users.items()}
        agents = []
        for a in f_agents.result()["data"]:
            at = a["attributes"]
            if at.get("isPreview") or not at.get("enabled"):
                continue
            agents.append({"id": a["id"], "name": at.get("name"), "description": at.get("description"),
                           "skills": at.get("customSkills") if at.get("skillsMode") == "custom" else ["all skills"],
                           "availableToAll": at.get("availableToAll"),
                           "groups": [g["id"] for g in a.get("relationships", {}).get("userGroups", {}).get("data", [])],
                           "conference": a["id"].startswith("conference-")})

    return {"host": f"https://{HOST}", "parent": PARENT_WS, "reportId": REPORT_ID, "workspaces": details,
            "themes": themes, "wdfs": wdfs, "groups": groups, "members": members, "agents": agents}


def _refresh():
    if not _cache_lock.acquire(blocking=False):
        return  # a refresh is already running
    try:
        _cache.update(t=time.time(), v=_build_overview())
    except Exception as e:  # keep serving the last good copy
        sys.stderr.write(f"overview refresh failed: {e}\n")
    finally:
        _cache_lock.release()


def overview(force=False):
    """Serve the cached overview at once; refresh it in the background when stale (or on ?refresh=1)."""
    if "v" not in _cache:
        with _cache_lock:
            if "v" not in _cache:
                _cache.update(t=time.time(), v=_build_overview())
        return _cache["v"]
    if force:
        _refresh()  # synchronous: the caller wants fresh data (e.g. after a change)
    elif time.time() - _cache["t"] > TTL:
        threading.Thread(target=_refresh, daemon=True).start()
    return _cache["v"]


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, fmt, *args):
        if "/gd/" in (args[0] if args else "") or "/app/" in (args[0] if args else ""):
            sys.stderr.write("%s %s\n" % (self.address_string(), fmt % args))

    def _json(self, obj, status=200):
        body = json.dumps(obj).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _route(self, method):
        url = urlparse(self.path)
        if url.path.startswith("/gd/"):
            return self._proxy(method, url)
        if method != "GET":
            return self._json({"error": "not found"}, 404)
        q = parse_qs(url.query)
        if url.path == "/app/personas":
            return self._json({"host": f"https://{HOST}", "parent": PARENT_WS, "reportId": REPORT_ID,
                               "personas": [{**p, "available": bool(token_for(p["id"]))} for p in PERSONAS]})
        if url.path == "/app/token":
            t = token_for(q.get("persona", [""])[0])
            return self._json({"token": t} if t else {"error": "no token for persona"}, 200 if t else 404)
        if url.path == "/app/overview":
            try:
                return self._json(overview(force=bool(q.get("refresh"))))
            except urllib.error.HTTPError as e:
                return self._json({"error": f"GoodData {e.code}", "detail": e.read().decode()[:500]}, 502)
        return self._static(url.path)

    def _static(self, path):
        f = (STATIC / (path.lstrip("/") or "index.html")).resolve()
        if not str(f).startswith(str(STATIC)) or not f.is_file():
            f = STATIC / "index.html"
        if not f.is_file():
            return self._json({"error": "UI not built: cd demo_app/web && npm run dev (or npm run build)"}, 404)
        body = f.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", mimetypes.guess_type(f.name)[0] or "application/octet-stream")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _proxy(self, method, url):
        token = token_for(self.headers.get("X-Persona", "admin"))
        if not token:
            return self._json({"error": "persona has no API token; run demo_app/setup_tokens.py"}, 401)
        length = int(self.headers.get("Content-Length") or 0)
        body = self.rfile.read(length) if length else None
        headers = {"Authorization": f"Bearer {token}", "Accept": self.headers.get("Accept", "*/*")}
        if self.headers.get("Content-Type"):
            headers["Content-Type"] = self.headers["Content-Type"]
        path = url.path[3:] + (f"?{url.query}" if url.query else "")
        conn = HTTPSConnection(HOST, timeout=300)
        try:
            conn.request(method, path, body=body, headers=headers)
            resp = conn.getresponse()
            self.send_response(resp.status)
            for h in ("Content-Type", "Content-Disposition"):
                if resp.getheader(h):
                    self.send_header(h, resp.getheader(h))
            self.send_header("Cache-Control", "no-store")
            self.send_header("Transfer-Encoding", "chunked")
            self.end_headers()
            while True:  # stream through (SSE chat responses arrive incrementally)
                chunk = resp.read1(16384)
                if not chunk:
                    break
                self.wfile.write(b"%x\r\n%s\r\n" % (len(chunk), chunk))
                self.wfile.flush()
            self.wfile.write(b"0\r\n\r\n")
        except (BrokenPipeError, ConnectionResetError):
            pass
        finally:
            conn.close()

    def do_GET(self):
        self._route("GET")

    def do_POST(self):
        self._route("POST")

    def do_PATCH(self):
        self._route("PATCH")

    def do_PUT(self):
        self._route("PUT")

    def do_DELETE(self):
        self._route("DELETE")


if __name__ == "__main__":
    srv = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    srv.daemon_threads = True
    print(f"Conference demo backend → http://127.0.0.1:{PORT}  (UI: cd demo_app/web && npm run dev → http://localhost:5173)")
    missing = [p["name"] for p in PERSONAS if not token_for(p["id"])]
    if missing:
        print(f"  ! no API token yet for: {', '.join(missing)} → run: python3 demo_app/setup_tokens.py")
    threading.Thread(target=lambda: overview(), daemon=True).start()  # warm the cache before the first page load
    srv.serve_forever()
