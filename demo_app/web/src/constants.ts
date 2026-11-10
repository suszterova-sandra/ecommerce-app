export const AGENT_STYLE: Record<string, { ico: string; bg: string; fg: string; short: string }> = {
  "conference-summary-agent": { ico: "🧾", bg: "#E0F2FE", fg: "#0369A1", short: "Summary" },
  "conference-next-steps-agent": { ico: "🧭", bg: "#FEF3C7", fg: "#B45309", short: "Next steps" },
  "conference-recommendations-agent": { ico: "💡", bg: "#EDE9FE", fg: "#6D28D9", short: "Recommendations" },
};

export const agentStyle = (id: string) => AGENT_STYLE[id] || { ico: "✦", bg: "#F1F5F9", fg: "#334155", short: "Assistant" };

export const PLAYBOOK = [
  {
    agent: "conference-summary-agent",
    title: "Summarize",
    sub: "What happened and why",
    prompt: "Summarize how this business performed over the last 3 months: net sales, orders, gross profit and active customers. What stands out?",
  },
  {
    agent: "conference-next-steps-agent",
    title: "Next steps",
    sub: "Who does what this week",
    prompt: "Based on these results, what should the team do in the next two weeks?",
  },
  {
    agent: "conference-recommendations-agent",
    title: "Recommendations",
    sub: "Levers with expected effect",
    prompt: "What are the top levers to grow net sales and gross profit next quarter? Back each one with data.",
  },
];

export const SKILL_LABEL: Record<string, string> = {
  visualization: "Visualization",
  key_driver_analysis: "Key drivers",
  alert: "Alerts",
  knowledge: "Knowledge",
  schedule_export: "Scheduled exports",
  anomaly_detection: "Anomalies",
  what_if_analysis: "What-if",
  forecasting: "Forecasting",
  metric: "Metrics",
  clustering: "Clustering",
  dashboard_builder: "Dashboard builder",
  dashboard_editor: "Dashboard editor",
  visualization_summary: "Viz summary",
  dashboard_summary: "Dashboard summary",
  report_builder: "Report builder",
  document_builder: "Document builder",
};

export const KEY_PERMS = ["MANAGE", "ANALYZE", "VIEW"];
