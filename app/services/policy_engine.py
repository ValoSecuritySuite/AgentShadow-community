"""Governance policy engine (forked verbatim from Valo).

Evaluates Policy definitions against a flat context dict and aggregates the
decisions into a single allow / warn / deny verdict (deny > warn > allow).
For AgentShadow the context is built from a scored agent rather than a prompt.
"""

import re
from typing import Any, Iterable

from app.schemas import (
    Policy,
    PolicyCondition,
    PolicyDecision,
    PolicyDecisionLiteral,
    PolicySet,
)

_DECISION_RANK: dict[str, int] = {"allow": 0, "warn": 1, "deny": 2}


def _get_nested(context: dict[str, Any], field_path: str) -> Any:
    parts = field_path.split(".")
    value: Any = context
    for part in parts:
        if isinstance(value, dict) and part in value:
            value = value[part]
        else:
            return None
    return value


def _evaluate_condition(context: dict[str, Any], condition: PolicyCondition) -> bool:
    actual = _get_nested(context, condition.field)
    expected = condition.value
    op = condition.op

    if op == "exists":
        return actual is not None
    if op == "not_exists":
        return actual is None
    if actual is None:
        return False
    if op == "eq":
        return actual == expected
    if op == "ne":
        return actual != expected
    if op == "in":
        return expected is not None and actual in expected
    if op == "not_in":
        return expected is None or actual not in expected
    if op == "contains":
        if isinstance(actual, (list, tuple, set)):
            return expected in actual
        if expected is None:
            return False
        return str(expected) in str(actual)
    if op == "matches":
        if expected is None:
            return False
        try:
            return bool(re.search(str(expected), str(actual)))
        except re.error:
            return False

    try:
        actual_num = float(actual)
        expected_num = float(expected) if expected is not None else 0.0
    except (TypeError, ValueError):
        return False

    if op == "gt":
        return actual_num > expected_num
    if op == "gte":
        return actual_num >= expected_num
    if op == "lt":
        return actual_num < expected_num
    if op == "lte":
        return actual_num <= expected_num
    return False


def _condition_reason(context: dict[str, Any], condition: PolicyCondition, matched: bool) -> str:
    actual = _get_nested(context, condition.field)
    status = "matched" if matched else "did not match"
    if condition.op in {"exists", "not_exists"}:
        return f"{condition.field} {condition.op} ({status})"
    return f"{condition.field} {condition.op} {condition.value!r} (actual={actual!r}, {status})"


def evaluate_policy(context: dict[str, Any], policy: Policy) -> PolicyDecision:
    if not policy.enabled:
        return PolicyDecision(
            policy_id=policy.id,
            name=policy.name,
            matched=False,
            decision="allow",
            severity=0,
            message=f"Policy '{policy.id}' is disabled",
            reasons=[],
            tags=list(policy.tags),
        )

    if not policy.when:
        all_matched = True
        reasons = ["no conditions defined: matches every context"]
    else:
        results = [(cond, _evaluate_condition(context, cond)) for cond in policy.when]
        all_matched = all(matched for _, matched in results)
        reasons = [_condition_reason(context, cond, matched) for cond, matched in results]

    decision: PolicyDecisionLiteral = policy.then.decision if all_matched else "allow"
    severity = policy.then.severity if all_matched else 0
    message = policy.then.message if all_matched else f"Policy '{policy.id}' did not match"

    return PolicyDecision(
        policy_id=policy.id,
        name=policy.name,
        matched=all_matched,
        decision=decision,
        severity=severity,
        message=message,
        reasons=reasons,
        tags=list(policy.tags),
    )


def evaluate_policies(context: dict[str, Any], policy_set: PolicySet) -> list[PolicyDecision]:
    return [evaluate_policy(context, policy) for policy in policy_set.policies]


def aggregate_decision(decisions: Iterable[PolicyDecision]) -> PolicyDecisionLiteral:
    final: PolicyDecisionLiteral = "allow"
    final_rank = _DECISION_RANK["allow"]
    for decision in decisions:
        if not decision.matched:
            continue
        rank = _DECISION_RANK.get(decision.decision, 0)
        if rank > final_rank:
            final = decision.decision
            final_rank = rank
    return final
