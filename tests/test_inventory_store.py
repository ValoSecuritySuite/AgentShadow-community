"""SQLite inventory store: upsert, filtering, retrieval, clearing."""

from app.schemas import AgentProfile
from app.services import inventory_store
from app.services.pipeline import score_agent


def _store(name: str, *, owner="platform", framework="langchain", tools=None) -> str:
    agent = score_agent(
        AgentProfile(name=name, owner=owner, framework=framework, tools=tools or [])
    )
    inventory_store.upsert_agent(agent)
    return agent.agent_id


def test_upsert_then_get_roundtrip():
    agent_id = _store("alpha")
    fetched = inventory_store.get_agent(agent_id)
    assert fetched is not None
    assert fetched.agent_id == agent_id
    assert fetched.name == "alpha"


def test_upsert_is_idempotent_and_bumps_scan_count():
    profile = AgentProfile(name="beta", owner="platform")
    a1 = score_agent(profile)
    is_new = inventory_store.upsert_agent(a1)
    assert is_new is True

    a2 = score_agent(profile)
    is_new_again = inventory_store.upsert_agent(a2)
    assert is_new_again is False

    stored = inventory_store.get_agent(a1.agent_id)
    assert stored is not None
    assert stored.scan_count == 2
    assert len(inventory_store.list_agents()) == 1


def test_filters_by_framework_and_owner():
    _store("crew-one", owner="team-a", framework="crewai")
    _store("lc-one", owner="team-b", framework="langchain")

    assert len(inventory_store.list_agents(framework="crewai")) == 1
    assert len(inventory_store.list_agents(owner="team-b")) == 1
    assert len(inventory_store.list_agents(framework="autogen")) == 0
    assert len(inventory_store.list_agents()) == 2


def test_clear_all_empties_inventory():
    _store("gamma")
    removed = inventory_store.clear_all()
    assert removed >= 1
    assert inventory_store.list_agents() == []


def test_results_sorted_by_risk_descending():
    _store("low", tools=["web_search"])
    _store("high", tools=["shell_exec", "code_interpreter", "filesystem"])
    agents = inventory_store.list_agents()
    scores = [a.risk_score for a in agents]
    assert scores == sorted(scores, reverse=True)
