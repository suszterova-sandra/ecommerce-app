"""Create or update the three conference agents in AI Hub (idempotent).

    python3 demo_app/setup_agents.py

Access is the demo point: the View group gets Summary and Next Steps only; Recommendations
(what-if, forecasting, clustering) is for the Analyze group and admins.
"""
import json
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ENV = dict(l.split("=", 1) for l in (ROOT / ".env").read_text().splitlines() if "=" in l)
TOKEN = ENV["GOODDATA_API_TOKEN"].strip().strip('"')
HOST = "https://navy-blue-eagle.trial.cloud.gooddata.com"


def req(method, path, body=None):
    r = urllib.request.Request(HOST + path, method=method, data=json.dumps(body).encode() if body else None,
                               headers={"Authorization": "Bearer " + TOKEN,
                                        "Content-Type": "application/vnd.gooddata.api+json"})
    try:
        with urllib.request.urlopen(r) as x:
            return x.status, x.read().decode()
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()


def ins(title, content):
    assert len(content) <= 255, (title, len(content))
    return {"title": title, "strategy": "ALWAYS", "content": content}


AGENTS = [
    dict(id="conference-summary-agent", name="Executive Summary Agent",
         description="Summarizes dashboards and visualizations in 5 bullets: what moved, by how much, and why it matters for this merchant.",
         personality="You are a crisp executive briefer for an ecommerce merchant. Lead with the headline number, then context. No jargon, no filler.",
         skills=["dashboard_summary", "visualization_summary", "visualization", "key_driver_analysis", "anomaly_detection"],
         instructions=[ins("Format", "Start with a one-line headline containing the key number. Then at most 5 bullets: metric, change vs previous period, and the main driver (category, brand, country or customer segment)."),
                       ins("Scope", "Only use governed metrics from this workspace. Always state the time period and filters used. Flag anomalies explicitly with the word 'Anomaly'.")],
         groups=["adminGroup", "analyze_group_id", "view_group_id"]),
    dict(id="conference-next-steps-agent", name="Next Steps Agent",
         description="Turns the current numbers into a short action plan: who does what this week, plus alerts and scheduled exports to keep watching.",
         personality="You are a pragmatic operations lead. You speak in actions with owners and deadlines, not in analysis.",
         skills=["visualization", "forecasting", "alert", "schedule_export", "visualization_summary", "dashboard_summary"],
         instructions=[ins("Format", "Return 3 numbered next steps. Each: action, owner role (Merchandising, Marketing, Ops, Finance), due date within 2 weeks, and the metric that proves it worked."),
                       ins("Follow-up", "After the steps, offer to create an alert on the metric to watch or to schedule a weekly export of the related dashboard. Ask before creating anything.")],
         groups=["adminGroup", "analyze_group_id", "view_group_id"]),
    dict(id="conference-recommendations-agent", name="Recommendations Agent",
         description="Finds the levers that move net sales and gross profit, and recommends what to change, with what-if estimates and forecasts.",
         personality="You are a senior ecommerce strategist. Recommendations must be backed by data: key drivers, what-if simulations or forecasts.",
         skills=["key_driver_analysis", "what_if_analysis", "forecasting", "clustering", "visualization", "metric"],
         instructions=[ins("Format", "Give at most 3 recommendations, ranked by impact. Each: the lever (price, discount, category mix, customer segment), the evidence, and 'Expected effect: <range>' from what-if or forecast."),
                       ins("Honesty", "If the effect cannot be estimated from the data, write 'effect not estimated' instead of guessing. Distinguish facts, interpretation and forecasts.")],
         groups=["adminGroup", "analyze_group_id"]),
]

if __name__ == "__main__":
    for a in AGENTS:
        body = {"data": {"id": a["id"], "type": "agent",
                         "attributes": {"enabled": True, "name": a["name"], "description": a["description"],
                                        "personality": a["personality"], "skillsMode": "custom",
                                        "customSkills": a["skills"], "aiKnowledge": True, "availableToAll": False,
                                        "instructions": a["instructions"]},
                         "relationships": {"userGroups": {"data": [{"id": g, "type": "userGroup"} for g in a["groups"]]}}}}
        s, t = req("POST", "/api/v1/entities/agents", body)
        if s == 409:
            s, t = req("PUT", "/api/v1/entities/agents/" + a["id"], body)
        print(a["id"], s, t[:300] if s >= 300 else "ok")
