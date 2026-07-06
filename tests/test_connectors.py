"""Runtime connectors: mock fleet + live OpenAI Assistants discovery."""

import httpx
import pytest

from app.connectors import openai_assistants
from app.connectors.openai_assistants import OpenAIAssistantsConnector


class _FakeResponse:
    def __init__(self, payload: dict):
        self._payload = payload

    def json(self) -> dict:
        return self._payload

    def raise_for_status(self) -> None:
        return None


class _FakeClient:
    """Stand-in for httpx.Client that serves a scripted sequence of pages."""

    def __init__(self, pages: list[dict], *args, **kwargs):
        self._pages = pages
        self.calls: list[dict] = []

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def get(self, url, headers=None, params=None):
        self.calls.append(params or {})
        idx = len([c for c in self.calls]) - 1
        return _FakeResponse(self._pages[idx])


def test_mock_fleet_when_no_api_key():
    connector = OpenAIAssistantsConnector()
    profiles = connector.discover(owner="ops")
    assert len(profiles) == 3
    assert all(p.source == "runtime" for p in profiles)
    assert all(p.metadata.get("mock") for p in profiles)
    names = {p.name for p in profiles}
    assert "Customer Support Assistant" in names


def test_live_discovery_follows_pagination(monkeypatch):
    pages = [
        {
            "data": [
                {"id": "asst_1", "name": "agent-one", "model": "gpt-4o", "tools": [{"type": "code_interpreter"}]},
            ],
            "has_more": True,
            "last_id": "asst_1",
        },
        {
            "data": [
                {"id": "asst_2", "name": "agent-two", "model": "gpt-4o-mini", "tools": [{"type": "file_search"}]},
            ],
            "has_more": False,
            "last_id": "asst_2",
        },
    ]
    created: dict = {}

    def _factory(*args, **kwargs):
        created["client"] = _FakeClient(pages, *args, **kwargs)
        return created["client"]

    monkeypatch.setattr(openai_assistants.httpx, "Client", _factory)

    connector = OpenAIAssistantsConnector()
    profiles = connector.discover(owner="ml", options={"api_key": "sk-test"})

    assert len(profiles) == 2
    assert {p.name for p in profiles} == {"agent-one", "agent-two"}
    assert all(p.metadata.get("live") for p in profiles)
    # file_search should be normalized to the canonical "filesystem" tool
    two = next(p for p in profiles if p.name == "agent-two")
    assert "filesystem" in two.tools
    # second page request must carry the cursor
    assert created["client"].calls[1].get("after") == "asst_1"


def test_live_failure_falls_back_to_mock(monkeypatch):
    def _boom(*args, **kwargs):
        raise httpx.ConnectError("network down")

    monkeypatch.setattr(openai_assistants.httpx, "Client", _boom)
    connector = OpenAIAssistantsConnector()
    profiles = connector.discover(owner="ops", options={"api_key": "sk-test"})
    assert len(profiles) == 3
    assert all(p.metadata.get("mock") for p in profiles)


def test_live_failure_raises_when_mock_disabled(monkeypatch):
    def _boom(*args, **kwargs):
        raise httpx.ConnectError("network down")

    monkeypatch.setattr(openai_assistants.httpx, "Client", _boom)
    connector = OpenAIAssistantsConnector()
    with pytest.raises(httpx.ConnectError):
        connector.discover(owner="ops", options={"api_key": "sk-test", "allow_mock": False})
