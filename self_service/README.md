# Emerald self-service setup

Emerald (call notes) wants dynamic metrics through parameters, user copies of developer dashboards, sharing of
user-created dashboards, and standard dashboards that nobody but the developers can change. Before object-level
permissions, VIEW was too restrictive and MANAGE let users delete dashboards. `setup_self_service.py` sets this up
on the two demo groups (idempotent):

```
python3 self_service/setup_self_service.py          # standard content + group permissions
python3 self_service/setup_self_service.py --demo   # + the Analyze user's copy, shared, and the checks below
```

**Standard content (parent workspace, developer-owned).** These are inherited by every show and shared view-only with all workspace users.
- String parameter **Sales measure** (`sales-measure`: Net Sales / Gross Sales / Gross Profit / Discounts), next to the
  existing **Currency** (string) and **Top N** (number) parameters.
- Metrics `selected_sales_measure` (CASE on the parameter) and `selected_sales_measure_top_n` (`TOP({parameter/top-n})`).
- Dashboard **5. Measure Explorer**: the three parameters on its filter bar, plus four visualizations and the Currency table.

**Groups (in Outdoor Retailer, where the demo users live)**

| Capability | Analyze Group | View Group |
|---|---|---|
| View standard dashboards, switch parameters | yes | yes |
| Use existing metrics (Analytical Designer, catalog) | yes (ANALYZE) | no |
| Create new metrics | yes (CREATE_METRIC): the open question from the call, drop it for re-use only | no |
| Copy dashboards ("Save as new"), ad hoc analytics | yes (new dashboards start private) | no |
| Share user-created dashboards | yes (owner shares View / Edit) | receives them |
| Edit or delete standard dashboards | no (they are defined in the parent; no MANAGE) | no |
| Filter views, alerts and schedules, export, AI assistant | yes | yes |

**Demo (`--demo`, run as the Analyze user).** The Analyze user creates the metric *Net Sales per Order (my metric)* and the
dashboard *My Measure Explorer (copy)*. The copy has Gross Profit pinned and an extra section. The Analyze user shares it with
the View Group (View) and the Analyze Group (Edit). Checks: the analyst opens the standard dashboard (200), but saving over it is refused (403). Both users open the copy (200), and the viewer cannot save over it (403).

Notes:
- Dashboard parameters are not supported in the YAML (analytics-as-code) format yet, so these objects live only in
  the workspace. After a `gd deploy` from `analytics/`, re-run this script.
- The Currency metric (`sales_converted_currency`) was private to its author. Tenant users could not see it or its table,
  so the script shares it view-only with all workspace users.
