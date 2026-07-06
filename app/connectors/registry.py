"""Connector registry + sync orchestration."""

from typing import Any

from app.connectors.base import Connector
from app.connectors.openai_assistants import OpenAIAssistantsConnector
from app.core.logging import get_logger
from app.schemas import Agent, ConnectorInfo
from app.services import inventory_store
from app.services.pipeline import score_agent
from app.services.rules_loader import load_rules

logger = get_logger(__name__)

_CONNECTORS: dict[str, Connector] = {
    c.id: c for c in (OpenAIAssistantsConnector(),)
}


def list_connectors() -> list[ConnectorInfo]:
    return [c.info() for c in _CONNECTORS.values()]


def get_connector(connector_id: str) -> Connector | None:
    return _CONNECTORS.get(connector_id)


def sync_connector(
    connector_id: str, owner: str = "unassigned", options: dict[str, Any] | None = None
) -> list[Agent]:
    connector = get_connector(connector_id)
    if connector is None:
        raise KeyError(connector_id)
    rules = load_rules()
    profiles = connector.discover(owner=owner, options=options or {})
    scored: list[Agent] = []
    for profile in profiles:
        agent = score_agent(profile, rules)
        inventory_store.upsert_agent(agent)
        scored.append(agent)
    logger.info("Connector '%s' synced %d agents", connector_id, len(scored))
    return scored
