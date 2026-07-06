"""Emit discovered agents to the shared Correlation Engine.

Implements the "add a new source" flow from the Valo demo stack README:
AgentShadow registers as source slug `agentshadow` and POSTs a signed
`IngestSignalEnvelope` per scored agent. Fire-and-forget: a correlation
failure never breaks discovery. Mirrors LLMShadow's `correlation_emitter`.
"""

import hashlib
import hmac
import json
import threading
from datetime import datetime, timezone
from typing import Any

import httpx

from app.core.config import get_settings
from app.core.logging import get_logger
from app.schemas import Agent

logger = get_logger(__name__)

_SEVERITY_BY_LEVEL = {
    "CRITICAL": "critical",
    "HIGH": "high",
    "MEDIUM": "medium",
    "LOW": "low",
    "MINIMAL": "info",
}


def _build_entities(agent: Agent) -> list[dict[str, Any]]:
    """Map an agent (and its findings) to correlation entities."""
    entities: list[dict[str, Any]] = [
        {
            "entity_type": "agent",
            "canonical_id": agent.agent_id,
            "finding_type": "ai_agent",
            "attributes": {
                "name": agent.name,
                "framework": agent.framework,
                "source": agent.source,
                "owner": agent.owner,
                "autonomy_level": agent.autonomy_level,
                "tool_count": agent.tool_count,
                "risk_score": agent.risk_score,
                "risk_level": agent.risk_level,
                "final_decision": agent.final_decision,
            },
        }
    ]
    for finding in agent.findings[:50]:
        entities.append(
            {
                "entity_type": "code_location",
                "canonical_id": f"{agent.agent_id}#{finding.rule_id}",
                "finding_type": finding.family or "agent_finding",
                "attributes": {
                    "rule_id": finding.rule_id,
                    "severity": finding.severity,
                    "evidence": finding.evidence,
                    "agent_id": agent.agent_id,
                },
            }
        )
    return entities


def _build_envelope(agent: Agent) -> dict[str, Any]:
    settings = get_settings()
    return {
        "source": settings.correlation_source_slug,
        "category": "other",
        "source_scan_id": agent.agent_id,
        "severity": _SEVERITY_BY_LEVEL.get(agent.risk_level, "info"),
        "risk_level": agent.risk_level,
        "risk_score": agent.risk_score,
        "occurred_at": datetime.now(timezone.utc).isoformat(),
        "summary": f"Agent '{agent.name}' ({agent.framework}) scored {agent.risk_score:.1f} [{agent.risk_level}]",
        "entities": _build_entities(agent),
        "raw_payload": {
            "agent_id": agent.agent_id,
            "framework": agent.framework,
            "final_decision": agent.final_decision,
            "finding_count": agent.finding_count,
        },
    }


def _sign(body: bytes, secret: str) -> dict[str, str]:
    signature = hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()
    return {"X-AgentShadow-Signature": signature}


def _post(envelope: dict[str, Any]) -> None:
    settings = get_settings()
    url = f"{settings.correlation_url.rstrip('/')}/ingest"
    body = json.dumps(envelope).encode("utf-8")
    headers = {"Content-Type": "application/json", **_sign(body, settings.correlation_secret)}
    try:
        resp = httpx.post(url, content=body, headers=headers, timeout=5.0)
        if resp.status_code >= 400:
            logger.warning("Correlation ingest returned %s: %s", resp.status_code, resp.text[:200])
    except Exception as exc:  # noqa: BLE001 - never fail discovery on correlation errors
        logger.warning("Correlation ingest failed: %s", exc)


def emit_agent(agent: Agent) -> None:
    """Fire-and-forget emit of a single scored agent to the correlation engine."""
    settings = get_settings()
    if not settings.correlation_enabled:
        return
    envelope = _build_envelope(agent)
    threading.Thread(target=_post, args=(envelope,), daemon=True).start()


def emit_agents(agents: list[Agent]) -> None:
    for agent in agents:
        emit_agent(agent)
