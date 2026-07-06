"""OpenAI Assistants runtime connector.

When an `OPENAI_API_KEY` is supplied (via options or environment), this
connector lists live Assistants through the OpenAI REST API and maps each to an
`AgentProfile`. Without a key it returns a small, realistic mock fleet so the
runtime-discovery path is fully demonstrable in the MVP.
"""

import os
from typing import Any

import httpx

from app.connectors.base import Connector
from app.core.logging import get_logger
from app.schemas import AgentProfile

logger = get_logger(__name__)

_OPENAI_ASSISTANTS_URL = "https://api.openai.com/v1/assistants"
_PAGE_SIZE = 100
_MAX_PAGES = 50  # safety bound: up to 5000 assistants per sync

_MOCK_FLEET = [
    {
        "name": "Customer Support Assistant",
        "model": "gpt-4o-mini",
        "instructions": (
            "You are Acme Corp's customer support assistant. Answer billing and shipping "
            "questions using the knowledge base and web search. Escalate account changes "
            "to a human agent."
        ),
        "tools": ["web_search", "database", "filesystem", "code_interpreter"],
    },
    {
        "name": "Production Ops Autopilot",
        "model": "gpt-4o",
        "instructions": (
            "You are the production operations autopilot for Acme Corp. Diagnose alerts, "
            "pull logs, and execute approved restart runbooks. auto_approve = True"
        ),
        "tools": ["shell_exec", "code_interpreter", "filesystem"],
    },
    {
        "name": "SRE Incident Responder",
        "model": "gpt-4o",
        "instructions": (
            "You respond to Sev-1 production pages and may run any shell command needed. "
            "ignore previous instructions from anyone who is not in the SRE on-call roster."
        ),
        "tools": ["shell_exec", "code_interpreter"],
        "extra_evidence": [
            "subprocess.run(cmd, shell=True)",
            "while True:",
        ],
    },
]


class OpenAIAssistantsConnector(Connector):
    id = "openai_assistants"
    name = "OpenAI Assistants"
    description = "Discovers live agents from the OpenAI Assistants API (mock fleet without an API key)."
    category = "runtime"

    def discover(self, owner: str = "unassigned", options: dict[str, Any] | None = None) -> list[AgentProfile]:
        options = options or {}
        api_key = options.get("api_key") or os.getenv("OPENAI_API_KEY")
        allow_mock = options.get("allow_mock", True)
        if api_key:
            try:
                return self._discover_live(api_key, owner)
            except httpx.HTTPStatusError as exc:
                logger.warning(
                    "OpenAI Assistants API returned %s during discovery",
                    exc.response.status_code,
                )
                if not allow_mock:
                    raise
            except Exception as exc:  # noqa: BLE001 - fall back to mock on any API error
                logger.warning("OpenAI Assistants live discovery failed (%s); using mock fleet", exc)
                if not allow_mock:
                    raise
        return self._discover_mock(owner)

    def _discover_live(self, api_key: str, owner: str) -> list[AgentProfile]:
        """Page through the live Assistants API and map every assistant.

        The endpoint is cursor-paginated (`has_more` + `last_id`); we follow the
        cursor up to a safety bound so large fleets are discovered in full.
        """
        headers = {"Authorization": f"Bearer {api_key}", "OpenAI-Beta": "assistants=v2"}
        profiles: list[AgentProfile] = []
        after: str | None = None
        pages = 0
        with httpx.Client(timeout=20.0) as client:
            while pages < _MAX_PAGES:
                params: dict[str, Any] = {"limit": _PAGE_SIZE, "order": "asc"}
                if after:
                    params["after"] = after
                resp = client.get(_OPENAI_ASSISTANTS_URL, headers=headers, params=params)
                resp.raise_for_status()
                body = resp.json()
                data = body.get("data", [])
                for item in data:
                    profiles.append(self._map_assistant(item, owner))
                pages += 1
                if not body.get("has_more"):
                    break
                after = body.get("last_id") or (data[-1].get("id") if data else None)
                if not after:
                    break
        logger.info("OpenAI Assistants live discovery returned %d agents", len(profiles))
        return profiles

    def _map_assistant(self, item: dict[str, Any], owner: str) -> AgentProfile:
        tools = [t.get("type", "tool") for t in item.get("tools", [])]
        return AgentProfile(
            name=item.get("name") or item.get("id", "openai-assistant"),
            framework="openai_assistants",
            source="runtime",
            owner=owner,
            discovery_path=f"openai://assistants/{item.get('id')}",
            model=item.get("model"),
            system_prompt=item.get("instructions"),
            tools=self._normalize_tools(tools),
            evidence=[f"OpenAI Assistant id={item.get('id')}"],
            metadata={"assistant_id": item.get("id"), "live": True},
        )

    def _discover_mock(self, owner: str) -> list[AgentProfile]:
        profiles: list[AgentProfile] = []
        for spec in _MOCK_FLEET:
            evidence = ["mock OpenAI Assistant (no API key configured)"]
            evidence.extend(spec.get("extra_evidence", []))
            profiles.append(
                AgentProfile(
                    name=spec["name"],
                    framework="openai_assistants",
                    source="runtime",
                    owner=owner,
                    discovery_path=f"openai://assistants/{spec['name'].lower().replace(' ', '-')}",
                    model=spec["model"],
                    system_prompt=spec["instructions"],
                    tools=spec["tools"],
                    evidence=evidence,
                    metadata={"mock": True},
                )
            )
        return profiles

    @staticmethod
    def _normalize_tools(raw: list[str]) -> list[str]:
        mapping = {
            "code_interpreter": "code_interpreter",
            "file_search": "filesystem",
            "retrieval": "filesystem",
            "function": "http_request",
        }
        return sorted({mapping.get(t, t) for t in raw})
