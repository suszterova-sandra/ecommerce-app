import json, os, time, urllib.request, pathlib
ROOT = pathlib.Path(__file__).resolve().parents[1]
for line in (ROOT / ".env").read_text().splitlines():
    if "=" in line and not line.startswith("#"):
        k, v = line.split("=", 1); os.environ.setdefault(k.strip(), v.strip().strip('"'))
HOST = "https://navy-blue-eagle.trial.cloud.gooddata.com"
TOKEN = os.environ["GOODDATA_API_TOKEN"]

def call(method, path, body=None, ctype="application/vnd.gooddata.api+json", accept="application/vnd.gooddata.api+json", raw=False):
    data = body if isinstance(body, (bytes, type(None))) else json.dumps(body).encode()
    req = urllib.request.Request(HOST + path, data=data, method=method, headers={
        "Authorization": f"Bearer {TOKEN}", "Content-Type": ctype, "Accept": accept})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=180) as r:
                out = r.read()
                if raw: return out
                return json.loads(out) if out else None
        except urllib.error.HTTPError as e:
            raise RuntimeError(f"{method} {path} -> {e.code}: {e.read().decode()[:500]}")
        except (ConnectionError, TimeoutError, urllib.error.URLError):
            if attempt == 2: raise
            time.sleep(3)
