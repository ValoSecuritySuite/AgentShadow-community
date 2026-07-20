#!/usr/bin/env bash
set -Eeuo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")"
chmod +x "$0" 2>/dev/null || true

if ! command -v docker >/dev/null 2>&1; then
  echo "Docker is required. Install/start Docker, then rerun this script." >&2
  exit 1
fi

if docker compose version >/dev/null 2>&1; then
  COMPOSE=(docker compose)
elif command -v docker-compose >/dev/null 2>&1; then
  COMPOSE=(docker-compose)
else
  echo "Docker Compose is required." >&2
  exit 1
fi

if [[ ! -f .env && -f .env.example ]]; then
  cp .env.example .env
fi

"${COMPOSE[@]}" up --build -d
echo "Waiting for AgentShadow Community API..."
for _ in {1..30}; do
  if "${COMPOSE[@]}" exec -T agentshadow-community python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" >/dev/null 2>&1; then
    break
  fi
  sleep 2
done
if "${COMPOSE[@]}" exec -T agentshadow-community python -m scripts.seed_demo >/dev/null 2>&1; then
  echo "Demo fleet seeded."
else
  echo "Services started; bundled seed command was not available."
fi
echo "AgentShadow Community is ready."
echo "Landing page: http://localhost:3011"
echo "Dashboard:    http://localhost:3011/dashboard"
echo "API:          http://localhost:8013"
echo "Docs:         http://localhost:8013/docs"
echo "Stop with: ${COMPOSE[*]} down"
