"""Scoring pipeline: deterministic risk + governance verdicts."""

from app.schemas import AgentProfile
from app.services.pipeline import build_artifact, build_context, score_agent


def _profile(**overrides) -> AgentProfile:
    base = dict(
        name="test-agent",
        framework="langchain",
        source="code",
        owner="platform",
        tools=[],
    )
    base.update(overrides)
    return AgentProfile(**base)


def test_high_risk_agent_scores_above_low_risk_agent():
    dangerous = _profile(
        name="devops-runner",
        tools=["shell_exec", "code_interpreter", "filesystem"],
        system_prompt="Operate production. You may run any shell command. auto_approve = True",
    )
    benign = _profile(name="faq-bot", tools=["web_search"], system_prompt="Answer FAQs politely.")

    hot = score_agent(dangerous)
    cold = score_agent(benign)

    assert hot.risk_score > cold.risk_score
    assert hot.risk_score >= cold.risk_score
    assert hot.risk_level in {"CRITICAL", "HIGH", "MEDIUM"}
    assert cold.risk_level in {"MINIMAL", "LOW", "MEDIUM"}


def test_score_is_deterministic():
    profile = _profile(tools=["shell_exec"], system_prompt="run shell commands")
    first = score_agent(profile)
    second = score_agent(profile)
    assert first.risk_score == second.risk_score
    assert first.risk_level == second.risk_level
    assert first.final_decision == second.final_decision


def test_context_flags_high_risk_tools():
    profile = _profile(tools=["shell_exec", "code_interpreter"])
    context = build_context(profile)
    assert context["has_shell_exec"] is True
    assert context["has_code_interpreter"] is True
    assert context["has_high_risk_tool"] is True
    assert context["tool_count"] == 2


def test_artifact_contains_prompt_and_tools():
    profile = _profile(tools=["database"], system_prompt="secret instructions")
    artifact = build_artifact(profile)
    assert "database" in artifact
    assert "secret instructions" in artifact


def test_agent_id_is_stable_and_slugified():
    profile = _profile(name="My Agent!", owner="Team Alpha")
    agent = score_agent(profile)
    assert agent.agent_id == "agent://team-alpha/my-agent"
    assert 0 <= agent.risk_score <= 100
