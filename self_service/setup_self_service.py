"""Emerald self-service setup: dynamic metrics with parameters, protected standard dashboards, and user-owned copies
that analysts can customise and share (idempotent, safe to re-run).

    python3 self_service/setup_self_service.py            # standard content + group permissions (admin .env)
    python3 self_service/setup_self_service.py --demo     # + the Analyze user's own copy, shared, and permission checks

Emerald's requirements (call notes) and how this setup meets them:

| Capability                         | Analyze group | View group | How                                                          |
|------------------------------------|---------------|------------|--------------------------------------------------------------|
| View standard dashboards           | yes           | yes        | parent dashboards, shared with all workspace users (VIEW)    |
| Switch calculations (parameters)   | yes           | yes        | Sales measure / Currency / Top N on the dashboard filter bar |
| Use existing metrics               | yes           | -          | ANALYZE (Analytical Designer, catalog)                       |
| Create new metrics                 | yes           | -          | CREATE_METRIC (the open question from the call: drop it to   |
|                                    |               |            | allow re-use only)                                           |
| Copy dashboards / ad hoc analytics | yes           | -          | ANALYZE: "Save as new" and new dashboards are private        |
| Share user-created dashboards      | yes           | receives   | owner shares VIEW / EDIT with users or groups                |
| Edit/delete standard dashboards    | no            | no         | defined in the parent: a child cannot change them; no MANAGE |
| Save filter views, alerts, exports | yes           | yes        | CREATE_FILTER_VIEW (in ANALYZE), CREATE_AUTOMATION, EXPORT   |
"""
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ENV = dict(l.split("=", 1) for l in (ROOT / ".env").read_text().splitlines() if "=" in l)
ADMIN = ENV["GOODDATA_API_TOKEN"].strip().strip('"')
USER_TOKENS = json.loads((ROOT / "demo_app" / ".tokens.json").read_text())
HOST = "https://navy-blue-eagle.trial.cloud.gooddata.com"
PARENT = "gdc_demo_a7c3afa0-ca91-40db-a3a8-df4d5044e92f"
TENANT = "gdc_demo_86a46377-cad8-4c3d-ab7c-6ba753b49b2c"  # Outdoor Retailer: where the demo users live
ANALYZE, VIEW = "analyze_group_id", "view_group_id"

GROUP_PERMISSIONS = {
    ANALYZE: ["ANALYZE", "CREATE_METRIC", "EXPORT", "CREATE_AUTOMATION", "USE_AI_ASSISTANT", "CREATE_DOCUMENT"],
    VIEW: ["VIEW", "CREATE_FILTER_VIEW", "EXPORT", "CREATE_AUTOMATION", "USE_AI_ASSISTANT"],
}


def api(method, path, body=None, token=ADMIN, ctype="application/vnd.gooddata.api+json"):
    r = urllib.request.Request(HOST + path, method=method, data=json.dumps(body).encode() if body is not None else None,
                               headers={"Authorization": "Bearer " + token, "Content-Type": ctype})
    try:
        with urllib.request.urlopen(r) as x:
            raw = x.read()
            return x.status, json.loads(raw) if raw else None
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()[:400]


def upsert(ws, kind, oid, attributes, token=ADMIN):
    body = {"data": {"id": oid, "type": kind[:-1], "attributes": attributes}}
    code, res = api("PUT", f"/api/v1/entities/workspaces/{ws}/{kind}/{oid}", body, token)
    if code == 404:
        code, res = api("POST", f"/api/v1/entities/workspaces/{ws}/{kind}", body, token)
    print(f"  {kind[:-1]} {oid}: {code}" + ("" if code < 300 else f" {res}"))
    return code


def ref(kind, oid):
    return {"identifier": {"type": kind, "id": oid}}


def measure(lid, metric, title):
    return {"measure": {"localIdentifier": lid, "title": title,
                        "definition": {"measureDefinition": {"item": ref("metric", metric), "filters": []}}}}


def attr(lid, label):
    return {"attribute": {"localIdentifier": lid, "displayForm": ref("label", label)}}


def viz(kind, measures, view=(), props=None):
    buckets = [{"localIdentifier": "measures", "items": list(measures)}]
    if view:  # the bucket name depends on the chart type: line charts read their axis from "trend"
        name = {"local:table": "attribute", "local:line": "trend", "local:area": "view"}.get(kind, "view")
        buckets.append({"localIdentifier": name, "items": list(view)})
    return {"version": "2", "visualizationUrl": kind, "buckets": buckets, "sorts": [], "filters": [],
            "properties": {"controls": props or {}}}


def widget(lid, vis, title, w, h):
    return {"type": "IDashboardLayoutItem", "size": {"xl": {"gridWidth": w, "gridHeight": h}},
            "widget": {"type": "insight", "localIdentifier": lid, "insight": ref("visualizationObject", vis),
                       "title": title, "description": "", "ignoreDashboardFilters": [], "drills": [],
                       "dateDataSet": ref("dataset", "date"), "properties": {},
                       "configuration": {"hideTitle": False}}}


def section(title, description, items):
    return {"type": "IDashboardLayoutSection", "header": {"title": title, "description": description}, "items": items}


def dashboard_content(fc_id, sections, parameters):
    return {"version": "2", "layout": {"type": "IDashboardLayout", "sections": sections},
            "filterContextRef": ref("filterContext", fc_id), "parameters": parameters, "plugins": []}


def filter_context(title):
    return {"title": title, "description": "", "content": {"version": "2", "filters": [
        {"dateFilter": {"localIdentifier": "0_dateFilter", "type": "relative", "granularity": "GDC.time.year",
                        "from": -1, "to": 0}},
        {"attributeFilter": {"localIdentifier": "product_category_filter", "displayForm": ref("label", "product_category"),
                             "negativeSelection": True, "attributeElements": {"uris": []}, "selectionMode": "multi"}}]}}


def share(ws, oid, rules, token=ADMIN, kind="analyticalDashboards"):
    code, res = api("POST", f"/api/v1/actions/workspaces/{ws}/{kind}/{oid}/managePermissions", rules,
                    token, "application/json")
    print(f"  share {oid}: {code}" + ("" if code < 300 else f" {res}"))


EVERYONE_VIEW = [{"assigneeRule": {"type": "allWorkspaceUsers"}, "permissions": ["VIEW"]}]


# ---------------------------------------------------------------- standard (developer) content in the parent
PARAMETERS = {
    "sales-measure": {
        "title": "Sales measure",
        "description": "Switches the measure behind the Measure Explorer: one metric instead of one per scenario.",
        "definition": {"type": "STRING", "defaultValue": "net_sales", "constraints": {"allowedValues": [
            {"value": "net_sales", "title": "Net Sales"}, {"value": "gross_sales", "title": "Gross Sales"},
            {"value": "gross_profit", "title": "Gross Profit"}, {"value": "discounts", "title": "Discounts"}]}},
    },
}

MONEY = "[>=1000000]$#,,.0 M;[>=1000]$#,.0 K;[>=0]$#,##0;[<=-1000000]-$#,,.0 M;[<=-1000]-$#,.0 K;[<0]-$#,##0"
METRICS = {
    "selected_sales_measure": {
        "title": "Sales (Selected Measure)",
        "description": "Net Sales, Gross Sales, Gross Profit or Discounts, chosen with the Sales measure parameter.",
        "maql": 'SELECT CASE\n'
                '  WHEN {parameter/sales-measure} = "net_sales" THEN {metric/net_sales}\n'
                '  WHEN {parameter/sales-measure} = "gross_sales" THEN {metric/total_sales}\n'
                '  WHEN {parameter/sales-measure} = "gross_profit" THEN {metric/gross_profit}\n'
                '  WHEN {parameter/sales-measure} = "discounts" THEN {metric/total_discounts}\n'
                '  ELSE NULL\nEND',
    },
    "selected_sales_measure_top_n": {
        "title": "Sales (Selected Measure, Top N)",
        "description": "The selected measure, limited to the Top N rows; N comes from the Top N parameter.",
        "maql": "SELECT {metric/selected_sales_measure} WHERE TOP({parameter/top-n}) OF ({metric/selected_sales_measure})",
    },
}

VISUALIZATIONS = {
    "measure_explorer_headline": ("Selected measure", viz("local:headline", [measure("m1", "selected_sales_measure", "Selected measure")])),
    "measure_explorer_by_category": ("Selected measure by product category", viz(
        "local:bar", [measure("m1", "selected_sales_measure", "Selected measure")], [attr("a1", "product_category")])),
    "measure_explorer_top_brands": ("Top N brands by selected measure", viz(
        "local:bar", [measure("m1", "selected_sales_measure_top_n", "Selected measure")], [attr("a1", "product_brand")])),
    "measure_explorer_trend": ("Selected measure by month", viz(
        "local:line", [measure("m1", "selected_sales_measure", "Selected measure")], [attr("a1", "date.month")])),
}

STANDARD_DASHBOARD = "measure_explorer"
STANDARD_SECTIONS = [
    section("Pick the measure", "One governed metric, switched with the Sales measure parameter on the filter bar. "
            "Currency converts sales; Top N sets how many brands are ranked.", [
        widget("w_headline", "measure_explorer_headline", "Selected measure", 3, 12),
        widget("w_trend", "measure_explorer_trend", "Selected measure by month", 9, 12)]),
    section("Where it comes from", "", [
        widget("w_category", "measure_explorer_by_category", "By product category", 4, 18),
        widget("w_brands", "measure_explorer_top_brands", "Top N brands", 4, 18),
        widget("w_currency", "b0552f35-fef5-4edd-9385-cb4258885283", "Sales in the selected currency", 4, 18)]),
]
STANDARD_PARAMETERS = [
    {"ref": ref("parameter", "sales-measure"), "parameterType": "STRING", "mode": "active"},
    {"ref": ref("parameter", "currency-rate"), "parameterType": "STRING", "mode": "active"},
    {"ref": ref("parameter", "top-n"), "parameterType": "NUMBER", "mode": "active", "value": 10},
]


def standard():
    print("Standard content (parent workspace, developer-owned)")
    for pid, a in PARAMETERS.items():
        upsert(PARENT, "parameters", pid, a)
    for mid, a in METRICS.items():
        upsert(PARENT, "metrics", mid, {"title": a["title"], "description": a["description"],
                                        "content": {"maql": a["maql"], "format": MONEY}})
    for vid, (title, content) in VISUALIZATIONS.items():
        upsert(PARENT, "visualizationObjects", vid, {"title": title, "content": content})
    fc = f"{STANDARD_DASHBOARD}_filterContext"
    upsert(PARENT, "filterContexts", fc, filter_context("Measure Explorer filters"))
    upsert(PARENT, "analyticalDashboards", STANDARD_DASHBOARD, {
        "title": "5. Measure Explorer",
        "description": "Standard dashboard: switch the measure, currency and Top N with parameters. "
                       "Read-only in every show; use Save as new to make your own copy.",
        "content": dashboard_content(fc, STANDARD_SECTIONS, STANDARD_PARAMETERS)})
    # standard content: everyone views, nobody but the developers edits. The Currency metric was private to its
    # author (object-level permissions), which hid its table from tenant users, so it is opened for viewing too.
    share(PARENT, STANDARD_DASHBOARD, EVERYONE_VIEW)
    for kind, oids in (("metrics", [*METRICS, "sales_converted_currency"]), ("visualizationObjects", VISUALIZATIONS)):
        for oid in oids:
            share(PARENT, oid, EVERYONE_VIEW, kind=kind)

    print(f"Group permissions in Outdoor Retailer ({TENANT})")
    code, layout = api("GET", f"/api/v1/layout/workspaces/{TENANT}/permissions")
    keep = [p for p in layout["permissions"] if p["assignee"]["id"] not in GROUP_PERMISSIONS]
    new = keep + [{"name": n, "assignee": {"id": g, "type": "userGroup"}}
                  for g, names in GROUP_PERMISSIONS.items() for n in names]
    code, res = api("PUT", f"/api/v1/layout/workspaces/{TENANT}/permissions",
                    {"permissions": new, "hierarchyPermissions": layout.get("hierarchyPermissions", [])},
                    ctype="application/json")
    print(f"  permissions: {code}" + ("" if code < 300 else f" {res}"))
    for g, names in GROUP_PERMISSIONS.items():
        print(f"  {g}: {', '.join(names)}")


# ---------------------------------------------------------------- the Analyze user's own copy, shared
COPY = "my_measure_explorer"


def demo():
    analyst, viewer = USER_TOKENS["sas.analyze.user"], USER_TOKENS["sas.view.user"]
    print("Analyze user: own metric, own copy of the standard dashboard, shared")
    upsert(TENANT, "metrics", "net_sales_per_order_custom", {
        "title": "Net Sales per Order (my metric)",
        "description": "Created by an analyst (CREATE_METRIC); the governed metrics stay untouched.",
        "content": {"maql": "SELECT {metric/net_sales} / {metric/number_of_orders}", "format": "$#,##0.00"}},
        analyst)
    upsert(TENANT, "visualizationObjects", "my_net_sales_per_order_by_brand", {
        "title": "Net sales per order by brand (my view)",
        "content": viz("local:column", [measure("m1", "net_sales_per_order_custom", "Net sales per order")],
                       [attr("a1", "product_brand")])}, analyst)
    fc = f"{COPY}_filterContext"
    upsert(TENANT, "filterContexts", fc, filter_context("My Measure Explorer filters"), analyst)
    sections = STANDARD_SECTIONS + [section("My analysis", "Added in my copy: a metric I created myself.", [
        widget("w_mine", "my_net_sales_per_order_by_brand", "Net sales per order by brand", 12, 18)])]
    params = [dict(p) for p in STANDARD_PARAMETERS]
    params[0]["value"] = "gross_profit"  # the copy pins its own default; the standard dashboard keeps Net Sales
    upsert(TENANT, "analyticalDashboards", COPY, {
        "title": "My Measure Explorer (copy)",
        "description": "The analyst's copy of 5. Measure Explorer: own default measure and an extra section.",
        "content": dashboard_content(fc, sections, params)}, analyst)
    share(TENANT, COPY, [{"assigneeIdentifier": {"id": VIEW, "type": "userGroup"}, "permissions": ["VIEW"]},
                         {"assigneeIdentifier": {"id": ANALYZE, "type": "userGroup"}, "permissions": ["EDIT"]}], analyst)

    print("Checks")
    std_path = f"/api/v1/entities/workspaces/{TENANT}/analyticalDashboards/{STANDARD_DASHBOARD}"
    code, std = api("GET", std_path, token=analyst)
    print(f"  analyst opens the standard dashboard: {code}")
    if code == 200:
        a = std["data"]["attributes"]
        body = {"data": {"id": STANDARD_DASHBOARD, "type": "analyticalDashboard",
                         "attributes": {"title": a["title"], "content": a["content"]}}}
        code, res = api("PUT", std_path, body, analyst)  # unchanged content: harmless even if it were accepted
        print(f"  analyst saves over the standard dashboard: {code} (expected 4xx)")
    copy_path = f"/api/v1/entities/workspaces/{TENANT}/analyticalDashboards/{COPY}"
    for who, tok in (("analyst", analyst), ("viewer", viewer)):
        code, cp = api("GET", copy_path, token=tok)
        print(f"  {who} opens the shared copy: {code}")
    if code == 200:
        a = cp["data"]["attributes"]
        body = {"data": {"id": COPY, "type": "analyticalDashboard", "attributes": {"title": a["title"], "content": a["content"]}}}
        print(f"  viewer saves over the shared copy: {api('PUT', copy_path, body, viewer)[0]} (expected 4xx)")
    code, _ = api("GET", f"/api/v1/actions/workspaces/{TENANT}/analyticalDashboards/{COPY}/permissions", token=ADMIN)
    print(f"  copy permissions: {_}")


if __name__ == "__main__":
    standard()
    if "--demo" in sys.argv:
        demo()
