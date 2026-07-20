#!/usr/bin/env bash
set -euo pipefail

test -f requirements.txt && test -f frontend/package.json || { echo "Run from the AgentShadow-community repository root."; exit 1; }

python -m pip install -r requirements.txt
test -d frontend/node_modules || npm --prefix frontend ci
if test -f scripts/seed_demo.py; then python -m scripts.seed_demo; fi

if ! curl -fsS http://127.0.0.1:8013/health >/dev/null 2>&1; then
  nohup env APP_EDITION=community APP_LOG_LEVEL=INFO \
    APP_CORRELATION_ENGINE_ENABLED=false APP_API_KEYS= \
    python -m uvicorn app.main:app --host 127.0.0.1 --port 8013 \
    >/tmp/agentshadow-community-api.log 2>&1 &
  echo $! >/tmp/agentshadow-community-api.pid
fi

for _ in $(seq 1 30); do curl -fsS http://127.0.0.1:8013/health >/dev/null 2>&1 && break; sleep 1; done
curl -fsS http://127.0.0.1:8013/health >/dev/null || { tail -n 200 /tmp/agentshadow-community-api.log; exit 1; }

if ! curl -fsS http://127.0.0.1:3011 >/dev/null 2>&1; then
  nohup env NEXT_PUBLIC_API_URL=http://127.0.0.1:8013 NEXT_PUBLIC_API_KEY= \
    NEXT_PUBLIC_EDITION=community NEXT_PUBLIC_UPGRADE_URL=/pricing \
    npm --prefix frontend run dev -- --hostname 127.0.0.1 --port 3011 \
    >/tmp/agentshadow-community-web.log 2>&1 &
  echo $! >/tmp/agentshadow-community-web.pid
fi

for _ in $(seq 1 45); do curl -fsS http://127.0.0.1:3011/dashboard >/dev/null 2>&1 && break; sleep 1; done
curl -fsS http://127.0.0.1:3011/dashboard >/dev/null || { tail -n 200 /tmp/agentshadow-community-web.log; exit 1; }
echo "AgentShadow Community demo ready: Dashboard http://localhost:3011/dashboard | API docs http://localhost:8013/docs"

