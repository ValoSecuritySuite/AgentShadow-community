#!/usr/bin/env bash
# One-command demo launcher for the AgentShadow Community Edition.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

API_URL="${AGENTSHADOW_API_URL:-http://localhost:8013}"
UI_URL="${AGENTSHADOW_UI_URL:-http://localhost:3011}"

echo "==> Starting AgentShadow Community Edition (Docker)..."
docker compose up --build -d

echo "==> Waiting for API health..."
for _ in $(seq 1 30); do
  if curl -sf "${API_URL}/health" >/dev/null 2>&1; then
    break
  fi
  sleep 2
done

if ! curl -sf "${API_URL}/health" >/dev/null 2>&1; then
  echo "ERROR: API did not become healthy at ${API_URL}/health" >&2
  exit 1
fi

echo "==> Seeding demo fleet (3 risk tiers: ~35% / ~60% / ~89%)..."
docker compose exec -T agentshadow-community python -m scripts.seed_demo

cat <<EOF

AgentShadow Community Edition is ready.

  Landing page (start here)  ${UI_URL}/
  Plans & pricing            ${UI_URL}/pricing
  Executive dashboard        ${UI_URL}/dashboard
  Agent inventory            ${UI_URL}/agents
  Scan a repo                ${UI_URL}/scan
  Governance policies        ${UI_URL}/governance

  API docs                   ${API_URL}/docs
  Health check               ${API_URL}/health
  Edition metadata           ${API_URL}/meta

Free in Community: code scan, scoring, inventory, dashboard, governance viewing.
Locked (upgrade):  runtime connectors, PDF reports, correlation feed.

Demo walkthrough:
  1. Open the landing page, then the dashboard — agents at ~35%, ~60%, and ~89% risk
  2. Agents → click SRE Incident Responder (CRITICAL); note the PDF export is a Pro upsell
  3. Scan → enter /app/sample_agents to discover the code-based demo agents (free)
  4. Scan → runtime connectors show as Pro-locked
  5. Pricing → compare Community vs Pro vs Enterprise

Stop:  docker compose down
Logs:  docker compose logs -f

EOF
