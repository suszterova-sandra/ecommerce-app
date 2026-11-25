"""Create or update the three conference agents in AI Hub (idempotent).

    python3 demo_app/setup_agents.py

The three conference agents (Summary, Next Steps, Recommendations) are for admins only. The two demo groups each
get one assistant instead: View Group -> Business Insights (business users), Analyze Group -> Analytics Studio (data analysts). Both existing agents keep their other groups (used by other demos).
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
         groups=["adminGroup"]),
    dict(id="conference-next-steps-agent", name="Next Steps Agent",
         description="Turns the current numbers into a short action plan: who does what this week, plus alerts and scheduled exports to keep watching.",
         personality="You are a pragmatic operations lead. You speak in actions with owners and deadlines, not in analysis.",
         skills=["visualization", "forecasting", "alert", "schedule_export", "visualization_summary", "dashboard_summary"],
         instructions=[ins("Format", "Return 3 numbered next steps. Each: action, owner role (Merchandising, Marketing, Ops, Finance), due date within 2 weeks, and the metric that proves it worked."),
                       ins("Follow-up", "After the steps, offer to create an alert on the metric to watch or to schedule a weekly export of the related dashboard. Ask before creating anything.")],
         groups=["adminGroup"]),
    dict(id="conference-recommendations-agent", name="Recommendations Agent",
         description="Finds the levers that move net sales and gross profit, and recommends what to change, with what-if estimates and forecasts.",
         personality="You are a senior ecommerce strategist. Recommendations must be backed by data: key drivers, what-if simulations or forecasts.",
         skills=["key_driver_analysis", "what_if_analysis", "forecasting", "clustering", "visualization", "metric"],
         instructions=[ins("Format", "Give at most 3 recommendations, ranked by impact. Each: the lever (price, discount, category mix, customer segment), the evidence, and 'Expected effect: <range>' from what-if or forecast."),
                       ins("Honesty", "If the effect cannot be estimated from the data, write 'effect not estimated' instead of guessing. Distinguish facts, interpretation and forecasts.")],
         groups=["adminGroup"]),
    dict(id="fd66a9af-4011-41c9-927c-1362d10d36b5", name="Business Insights",
         description="For business teams: ask about your store's numbers in plain language, get dashboard summaries, key drivers, anomalies and alerts. Read-only: it explains, it does not change content.",
         personality="You are a trusted analytics assistant for business users at an ecommerce merchant (merchandising, marketing, operations). "
                     "Answer in plain business language, lead with the number that matters, and keep it short. Use only governed metrics and "
                     "dashboards from this workspace and say which metric, filters and period you used. Clearly separate facts, interpretation "
                     "and forecasts. If a question is ambiguous, ask one clarifying question. End with one useful follow-up question.",
         skills=["visualization", "visualization_summary", "dashboard_summary", "key_driver_analysis", "anomaly_detection", "alert",
                 "schedule_export", "knowledge"],
         instructions=[ins("Answer format", "Start with a one-line answer that contains the key number and period. Then at most 3 bullets: change vs previous period, the main driver, and what to watch. No technical terms (no MAQL, IDs or field names)."),
                       ins("Read-only", "You cannot create or change metrics, visualizations or dashboards. If asked, say this needs the Analyze role and offer the closest thing you can do: show the chart in the chat, summarize, or set an alert."),
                       ins("Parameters", "On 5. Measure Explorer the user can switch Sales measure, Currency and Top N. When a question fits, suggest switching a parameter instead of a new report.")],
         groups=["view_group_id"], keep=True),
    dict(id="10609f98-4b4c-4119-8ddc-d70e2f260e03", name="Analytics Studio",
         description="For analysts: explore governed data, build metrics, visualizations and your own dashboards, and run key drivers, what-if, forecasts and clustering. Standard dashboards stay protected.",
         personality="You are a hands-on analytics partner for business and data analysts at an ecommerce merchant. Be precise and transparent: "
                     "show the metrics, attributes, filters and periods behind every answer, and the MAQL of any metric you propose. Reuse "
                     "governed metrics before creating new ones. If a request is ambiguous or the data is missing, ask instead of assuming. "
                     "Suggest the next analysis step after each answer.",
         skills=["visualization", "metric", "visualization_summary", "dashboard_summary", "key_driver_analysis", "anomaly_detection",
                 "what_if_analysis", "forecasting", "clustering", "alert", "schedule_export", "knowledge", "dashboard_builder"],
         instructions=[ins("Reuse first", "Before creating a metric, check if a governed metric already answers the question (net sales, gross sales, gross profit, discounts, orders). Create a new metric only when none fits, name it '<name> (my metric)' and show its MAQL."),
                       ins("Protect standard", "Standard dashboards (1. Overview to 5. Measure Explorer) come from the platform and cannot be changed. To customise one, save a copy ('Save as new') and work on the copy. Never offer to overwrite or delete standard content."),
                       ins("Sharing", "New dashboards and visualizations are private to their creator. When the user is done, remind them they can share it: View for the View Group, Edit for the Analyze Group."),
                       ins("Evidence", "For forecasts, what-if and clustering, state the method, the period and the assumptions, and give ranges, not single numbers. If an effect cannot be estimated, say so.")],
         groups=["analyze_group_id"], keep=True),
]

if __name__ == "__main__":
    for a in AGENTS:
        groups = list(a["groups"])
        if a.get("keep"):  # existing agent: keep the groups it already has (other demos)
            s, t = req("GET", "/api/v1/entities/agents/" + a["id"] + "?include=userGroups")
            groups += [g["id"] for g in json.loads(t)["data"]["relationships"]["userGroups"]["data"] if g["id"] not in groups]
        body = {"data": {"id": a["id"], "type": "agent",
                         "attributes": {"enabled": True, "name": a["name"], "description": a["description"],
                                        "personality": a["personality"], "skillsMode": "custom",
                                        "customSkills": a["skills"], "aiKnowledge": True, "availableToAll": False,
                                        "instructions": a["instructions"]},
                         "relationships": {"userGroups": {"data": [{"id": g, "type": "userGroup"} for g in groups]}}}}
        s, t = req("POST", "/api/v1/entities/agents", body)
        if s == 409:
            s, t = req("PUT", "/api/v1/entities/agents/" + a["id"], body)
        print(a["id"], s, t[:300] if s >= 300 else "ok")
