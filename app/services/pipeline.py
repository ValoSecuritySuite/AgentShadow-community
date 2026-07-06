"""Agent scoring pipeline.

Treats each agent's configuration + behaviour as the scannable artifact
(the same way Valo treats a prompt). Flow:

    AgentProfile -> artifact text + metadata context
                 -> text-scan engine + context-rule engine  (Valo rule engine)
                 -> deterministic combined score             (cvss_combined_score)
                 -> governance policy evaluation             (Valo policy engine)
                 -> scored Agent (ready for inventory)
"""

from typing import Any

from app.detectors.agent_frameworks import _HIGH_RISK_TOOLS, estimate_autonomy
from app.schemas import (
    Agent,
    AgentProfile,
    PolicyDecision,
    RuleSet,
    TextFinding,
)
from app.services import policy_engine, rule_engine
from app.services.policy_store import load_policies
from app.services.rules_loader import load_rules

_RISK_BANDS: list[tuple[float, str, str]] = [
    (80.0, "CRITICAL", "F"),
    (60.0, "HIGH", "D"),
    (40.0, "MEDIUM", "C"),
    (20.0, "LOW", "B"),
    (0.0, "MINIMAL", "A"),
]


def _risk_band(score: float) -> tuple[str, str]:
    for threshold, level, grade in _RISK_BANDS:
        if score >= threshold:
            return level, grade
    return "MINIMAL", "A"


def build_artifact(profile: AgentProfile) -> str:
    """Concatenate the agent's scannable surface into a single text blob."""
    parts: list[str] = [
        f"framework: {profile.framework}",
        f"model: {profile.model or 'unknown'}",
        f"autonomy_level: {profile.autonomy_level}",
        f"tools: {', '.join(profile.tools) if profile.tools else 'none'}",
    ]
    if profile.system_prompt:
        parts.append("system_prompt:\n" + profile.system_prompt)
    if profile.evidence:
        parts.append("evidence:\n" + "\n".join(profile.evidence))
    return "\n".join(parts)


def build_context(profile: AgentProfile) -> dict[str, Any]:
    """Flat context dict for the context-rule engine and policy engine."""
    tools = set(profile.tools)
    autonomy = profile.autonomy_level
    if autonomy == "unknown":
        autonomy = estimate_autonomy(tools)
    context: dict[str, Any] = {
        "framework": profile.framework,
        "source": profile.source,
        "owner": profile.owner,
        "autonomy_level": autonomy,
        "tool_count": len(tools),
        "model": profile.model or "unknown",
        "has_shell_exec": "shell_exec" in tools,
        "has_code_interpreter": "code_interpreter" in tools,
        "has_high_risk_tool": bool(tools & _HIGH_RISK_TOOLS),
    }
    for tool in tools:
        context[f"tool_{tool}"] = True
    return context


def score_agent(profile: AgentProfile, rule_set: RuleSet | None = None) -> Agent:
    """Run the full pipeline and return a scored, governance-evaluated Agent."""
    rules = rule_set or load_rules()
    artifact = build_artifact(profile)
    context = build_context(profile)

    # Stage: text-scan engine over the artifact (Valo engine)
    txt = rule_engine.scan_text(artifact, rules)
    # Stage: context rules over agent metadata (Valo engine)
    ctx = rule_engine.evaluate(context, rules)
    # Stage: deterministic combined score (Valo locked model)
    combined = rule_engine.cvss_combined_score(ctx.total_score, txt.findings, rules.text_scan_rules)
    max_sev, _ = rule_engine.severity_info(txt.findings)

    risk_level, posture_grade = _risk_band(combined)

    # Stage: governance policies (Valo policy engine)
    policy_context = _policy_context(profile, context, combined, max_sev, txt.findings)
    decisions: list[PolicyDecision] = policy_engine.evaluate_policies(
        policy_context, load_policies()
    )
    final_decision = policy_engine.aggregate_decision(decisions)

    return Agent(
        agent_id=profile.agent_id(),
        name=profile.name,
        framework=profile.framework,
        source=profile.source,
        owner=profile.owner,
        discovery_path=profile.discovery_path,
        model=profile.model,
        autonomy_level=context["autonomy_level"],
        tools=sorted(profile.tools),
        tool_count=len(profile.tools),
        risk_score=combined,
        risk_level=risk_level,
        max_severity=max_sev,
        posture_grade=posture_grade,
        final_decision=final_decision,
        finding_count=len(txt.findings),
        findings=txt.findings,
        policy_decisions=decisions,
        metadata={**profile.metadata, "context": context},
    )


def _policy_context(
    profile: AgentProfile,
    context: dict[str, Any],
    risk_score: float,
    max_severity: int,
    findings: list[TextFinding],
) -> dict[str, Any]:
    finding_families = sorted({f.family for f in findings if f.family})
    finding_rule_ids = sorted({f.rule_id for f in findings})
    return {
        **context,
        "agent_id": profile.agent_id(),
        "name": profile.name,
        "target": profile.agent_id(),
        "risk_score": risk_score,
        "combined_score": risk_score,
        "max_severity": max_severity,
        "finding_count": len(findings),
        "finding_families": finding_families,
        "finding_rule_ids": finding_rule_ids,
    }
