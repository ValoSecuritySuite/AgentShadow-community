"""Runtime/SaaS agent-discovery connector interface.

Mirrors the SaaSShadow connector pattern: a connector knows how to enumerate
live agents from a provider (OpenAI Assistants API, a hosted CrewAI/LangServe
deployment, etc.) and returns framework-agnostic `AgentProfile` objects that
the scoring pipeline can ingest. The MVP ships a fully working mock connector
so the runtime-discovery path is demonstrable without external credentials;
real connectors implement the same `discover()` contract.
"""

from abc import ABC, abstractmethod
from typing import Any

from app.schemas import AgentProfile, ConnectorInfo


class Connector(ABC):
    id: str = "base"
    name: str = "Base connector"
    description: str = "Abstract connector"
    category: str = "runtime"

    def info(self) -> ConnectorInfo:
        return ConnectorInfo(
            id=self.id, name=self.name, description=self.description, category=self.category
        )

    @abstractmethod
    def discover(self, owner: str = "unassigned", options: dict[str, Any] | None = None) -> list[AgentProfile]:
        """Return the agents this connector can currently see at runtime."""
        raise NotImplementedError
