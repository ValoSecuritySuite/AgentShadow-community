# AgentShadow — Community Edition

**Free, self-hosted discovery and risk scoring for the AI agents in your codebase.**

The AgentShadow Community Edition scans your source code for AI agent frameworks
(LangChain/LangGraph, CrewAI, AutoGPT, AutoGen, OpenAI Assistants, LlamaIndex,
Semantic Kernel), scores each agent's risk deterministically, and shows it all in
an executive dashboard with governance policies — **completely free**.

It is a trimmed edition of the full [AgentShadow](../AgentShadow) product, and it
doubles as a live advert: the premium capabilities are present but locked behind
an in-app upgrade so you can see exactly what Pro and Enterprise add.

## What's included vs. what's locked

| Capability | Community (free) | Pro | Enterprise |
|---|:---:|:---:|:---:|
| Source-code agent discovery | ✅ | ✅ | ✅ |
| Deterministic 0–100 risk scoring | ✅ | ✅ | ✅ |
| Agent inventory + executive dashboard | ✅ | ✅ | ✅ |
| Governance policy viewing | ✅ | ✅ | ✅ |
| Runtime & SaaS connectors (live cloud discovery) | 🔒 | ✅ | ✅ |
| Branded PDF assessment reports | 🔒 | ✅ | ✅ |
| API access control | 🔒 | ✅ | ✅ |
| Correlation engine feed (cross-tool asset graph) | 🔒 | — | ✅ |
| SSO, custom connectors, priority support | 🔒 | — | ✅ |

Locked features appear in the UI with a **PRO**/**ENTERPRISE** badge and an
upgrade CTA, and the API returns HTTP `402` with an upgrade payload if called.
See in-app **Pricing** at `/pricing` (linked from the sidebar and landing page).

> Runs on its own ports (API **8013**, UI **3011**) so it can sit alongside the
> full AgentShadow stack (8003 / 3001) on the same machine.

## Quick start (local dev)

Backend (FastAPI, Python 3.12):

```bash
cd agentshadow-community
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m scripts.seed_demo          # optional: populate a demo agent fleet
uvicorn app.main:app --reload --port 8013
```

- API: http://localhost:8013 · health: `/health` · edition: `/meta` · docs: `/docs`

Frontend (Next.js 15):

```bash
cd agentshadow-community/frontend
npm install
NEXT_PUBLIC_API_URL=http://localhost:8013 npm run dev -- --port 3011
```

- Landing page: http://localhost:3011/
- Pricing / upgrade: http://localhost:3011/pricing
- Dashboard: http://localhost:3011/dashboard

## Quick start (Docker)

```bash
cd agentshadow-community
cp .env.example .env
docker compose up --build
# API http://localhost:8013 · UI http://localhost:3011 (landing) · pricing /pricing
```

Or use the one-command launcher (starts the stack and seeds the demo fleet):

```bash
./start.sh
```

## Editions at runtime

The edition is controlled by `APP_EDITION` (backend) and `NEXT_PUBLIC_EDITION`
(frontend), both defaulting to `community`:

```bash
# Unlock everything (e.g. for evaluating the full product or running the tests)
APP_EDITION=pro uvicorn app.main:app --reload --port 8013
```

The backend exposes the edition catalogue at `GET /meta`, which the frontend uses
to decide which features to render as locked.

## Testing

```bash
cd agentshadow-community
pip install -r requirements-dev.txt
pytest
```

The suite covers the scoring pipeline, SQLite inventory store, connectors, the
REST API, access control, and the Community Edition gating (locked endpoints
return `402`; `/meta` reports the edition).

## Key API endpoints

| Method | Path | Purpose | Community |
|---|---|---|:---:|
| GET | `/health` | Liveness | ✅ |
| GET | `/meta` | Edition + locked-feature catalogue | ✅ |
| POST | `/scan/repository` | Code discovery: `{ "path": "...", "owner": "..." }` | ✅ |
| GET | `/agents/discovered` | Inventory (filters: framework, source, risk_level, owner) | ✅ |
| GET | `/agents/detail?agent_id=` | Single agent | ✅ |
| GET | `/dashboard/overview` | Executive KPIs + distributions | ✅ |
| GET | `/policies` | Governance policies | ✅ |
| GET | `/connectors` | List runtime connectors (shown locked) | ✅ |
| POST | `/connectors/{id}/sync` | Runtime discovery | 🔒 402 |
| POST | `/report/pdf?agent_id=` | Branded PDF assessment | 🔒 402 |

## Upgrade

Ready for live cloud discovery, PDF reporting, and the shared correlation graph?
Open **Pricing** in the app (`/pricing`) or run the full
[AgentShadow](../AgentShadow) product.
