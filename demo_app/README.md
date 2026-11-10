# Conference demo app

React (Vite + TypeScript) shell around the **Ecommerce (Conference)** workspaces on
`navy-blue-eagle.trial.cloud.gooddata.com`, built to show one parent with three branded tenants, switching
between users with their real permissions, the embedded AI report, and AI Hub agents.

## Run

```bash
# once
python3 demo_app/setup_agents.py     # creates/updates the 3 conference agents in AI Hub (idempotent)
python3 demo_app/setup_tokens.py     # API tokens for sas.analyze.user + sas.view.user -> demo_app/.tokens.json
cd demo_app/web && npm install

# every time (two terminals)
python3 demo_app/server.py          # backend on 127.0.0.1:8765 (tokens + GoodData proxy)
cd demo_app/web && npm run dev                 # UI on http://localhost:5173
```

Port 5173 is one of the org's allowed embedding origins, so keep it.
`npm run build` produces `web/dist`, which `server.py` also serves on :8765.

## What it shows

| Screen | Story |
|---|---|
| **Home** | Portal welcome page for the selected workspace: what happened last quarter, live KPIs, the key drivers behind the change (each opens the dashboard at the right visualization), an AI briefing, and the GoodData AI Assistant with the agents provisioned for the current user. |
| **Control Center** (admin only) | Parent → 3 tenants, each card in its own GoodData theme, with its data filter values (`wdf__client_id`, `wdf__product_category`), inherited content and who has access. Access matrix per user, AI Hub agent matrix per user. "View as →" jumps into a user. |
| **Dashboards** | goodsalesv4's catalog: **Shared** and **Private** dashboards (`accessInfo.private`), a `tenant` tag for dashboards created in the child, and **+ New dashboard** for users with ANALYZE (a blank GoodData dashboard in edit mode; after Save the app re-reads the catalog and opens the new dashboard). Above each dashboard an **agentic summary** (Summary / Key points / Areas to watch); clicking a key point runs key driver analysis inline. |
| **AI Report** | The `ecommerce_business_report` document embedded; authored in the parent, inherited and re-themed by every tenant. **Export PDF** runs the document export as the current user. |
| **Analyze** | Analytical Designer for users with ANALYZE; the View user gets a locked screen that explains why. |
| **AI Agents** | Agents the current user can reach in this workspace (`GET /api/v1/ai/workspaces/{ws}/agents`), plus the conference agents they can't reach. Playbook: Summarize → Next steps → Recommendations, or **Run the chain** to hand one conversation from agent to agent (`switchAgent`). Answers stream from the AI Assistant API. |

## AI Assistant panel

Ported from goodsalesv4 (`AIAssistant`, `ChatbotOverlay`, `AppLayout`): GoodData's own `GenAIAssistant`
(`@gooddata/sdk-ui-gen-ai` 11.66.0) docked on the right with a collapsible conversation history and a new-chat
button, opened from the top bar, the "Ask AI" launcher, the Home banner, the agentic summary and key driver
results. Each open starts a fresh conversation with the open dashboard as context. The backend is built per
user from that user's API token, so switching users switches the assistant, its agents and its history.

## Users and access

| User | Group | Clothing workspace | Conference agents |
|---|---|---|---|
| Admin (`sandra.suszterova`) | admin | MANAGE (org) | all three |
| `sas.analyze.user` | Analyze Group | ANALYZE, metrics, export, automations, AI | Summary, Next steps, Recommendations |
| `sas.view.user` | View Group | VIEW, filter views, export, automations, AI | Summary, Next steps (Recommendations is locked) |

## How access is enforced

Nothing is filtered in the front end. Every `/gd/...` call carries `X-Persona`; `server.py` swaps in that
user's API token and proxies to GoodData, so workspace lists, permissions, agents and AI answers come back
exactly as GoodData resolves them for that user. Embedded iframes use the same token through GoodData's
`listeningForApiToken` → `setApiToken` postMessage handshake (`src/api.ts`).

The server binds to 127.0.0.1 and hands tokens to the browser: keep it local.

