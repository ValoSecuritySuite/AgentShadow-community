"""Deterministic rule + text-scan engine.

Forked verbatim from Valo (`valo/app/services/rule_engine.py`) so AgentShadow
reuses the exact, locked scoring model. The only conceptual change is the
*input* it scores: an agent's configuration + behaviour artifact rather than a
raw prompt.
"""

import math
import re
from typing import Any

from app.schemas import (
    Pattern,
    Rule,
    RuleEngineResult,
    RuleMatch,
    RuleSet,
    TextFinding,
    TextScanResult,
    TextScanRule,
)


def _get_nested(context: dict[str, Any], field_path: str) -> Any:
    parts = field_path.split(".")
    value: Any = context
    for part in parts:
        if isinstance(value, dict) and part in value:
            value = value[part]
        else:
            return None
    return value


def _evaluate_pattern(context: dict[str, Any], pattern: Pattern) -> bool:
    actual = _get_nested(context, pattern.field)
    expected = pattern.value
    op_ = pattern.op

    if op_ == "exists":
        return actual is not None
    if op_ == "not_exists":
        return actual is None
    if actual is None:
        return False
    if op_ == "eq":
        return actual == expected
    if op_ == "neq":
        return actual != expected
    if op_ == "in":
        return expected is not None and actual in expected
    if op_ == "not_in":
        return expected is None or actual not in expected

    actual_str = str(actual)
    if op_ == "contains":
        return expected is not None and str(expected) in actual_str
    if op_ == "not_contains":
        return expected is None or str(expected) not in actual_str
    if op_ == "matches":
        if expected is None:
            return False
        try:
            return bool(re.fullmatch(str(expected), actual_str))
        except re.error:
            return False

    try:
        actual_num = float(actual)
        expected_num = float(expected) if expected is not None else 0.0
    except (TypeError, ValueError):
        return False

    if op_ == "gte":
        return actual_num >= expected_num
    if op_ == "lte":
        return actual_num <= expected_num
    if op_ == "gt":
        return actual_num > expected_num
    if op_ == "lt":
        return actual_num < expected_num
    return False


def _rule_matches(context: dict[str, Any], rule: Rule) -> bool:
    if not rule.enabled:
        return False
    if not rule.patterns:
        return True
    return all(_evaluate_pattern(context, pattern) for pattern in rule.patterns)


def _normalize_score(matched_weight: float, enabled_weight_total: float) -> float:
    if enabled_weight_total <= 0:
        return 0.0
    normalized = (matched_weight / enabled_weight_total) * 100.0
    return round(min(max(normalized, 0.0), 100.0), 2)


def evaluate(context: dict[str, Any], rule_set: RuleSet) -> RuleEngineResult:
    """Evaluate context against context rules in list order (deterministic)."""
    matched_rules: list[RuleMatch] = []
    matched_weight_total = 0.0
    enabled_weight_total = 0.0
    passed = 0
    failed = 0

    for rule in rule_set.rules:
        if rule.enabled:
            enabled_weight_total += rule.weight
        matched = _rule_matches(context, rule)
        matched_rules.append(
            RuleMatch(
                rule_name=rule.name,
                severity=rule.severity,
                weight=rule.weight,
                matched=matched,
            )
        )
        if matched:
            passed += 1
            matched_weight_total += rule.weight
        else:
            failed += 1

    total_score = _normalize_score(matched_weight_total, enabled_weight_total)
    return RuleEngineResult(
        matched_rules=matched_rules,
        total_score=total_score,
        passed_count=passed,
        failed_count=failed,
    )


# ── Text-scan engine ─────────────────────────────────────────────────────────

_EVIDENCE_CONTEXT = 40


def _extract_evidence(text: str, start: int, end: int) -> str:
    ctx_start = max(0, start - _EVIDENCE_CONTEXT)
    ctx_end = min(len(text), end + _EVIDENCE_CONTEXT)
    prefix = "..." if ctx_start > 0 else ""
    suffix = "..." if ctx_end < len(text) else ""
    return f"{prefix}{text[ctx_start:ctx_end]}{suffix}"


def _scan_regex_rule(text: str, rule: TextScanRule) -> list[TextFinding]:
    findings: list[TextFinding] = []
    try:
        for match in re.finditer(rule.pattern, text, re.IGNORECASE | re.MULTILINE):
            start, end = match.start(), match.end()
            findings.append(
                TextFinding(
                    rule_id=rule.id,
                    family=rule.family,
                    category=rule.category,
                    severity=rule.severity,
                    weight=rule.weight,
                    evidence=_extract_evidence(text, start, end),
                    match_start=start,
                    match_end=end,
                )
            )
    except re.error:
        pass
    return findings


def _scan_keyword_rule(text: str, rule: TextScanRule) -> list[TextFinding]:
    findings: list[TextFinding] = []
    lower_text = text.lower()
    keyword = rule.pattern.lower()
    if not keyword:
        return findings
    start = 0
    while True:
        idx = lower_text.find(keyword, start)
        if idx == -1:
            break
        end = idx + len(keyword)
        findings.append(
            TextFinding(
                rule_id=rule.id,
                family=rule.family,
                category=rule.category,
                severity=rule.severity,
                weight=rule.weight,
                evidence=_extract_evidence(text, idx, end),
                match_start=idx,
                match_end=end,
            )
        )
        start = end
    return findings


def _shannon_entropy(data: str) -> float:
    if not data:
        return 0.0
    freq: dict[str, int] = {}
    for ch in data:
        freq[ch] = freq.get(ch, 0) + 1
    length = len(data)
    return -sum((count / length) * math.log2(count / length) for count in freq.values())


def _scan_entropy_rule(text: str, rule: TextScanRule) -> list[TextFinding]:
    try:
        threshold = float(rule.pattern) if rule.pattern else 4.5
    except ValueError:
        threshold = 4.5
    findings: list[TextFinding] = []
    for match in re.finditer(r"\S{8,}", text):
        token = match.group()
        if _shannon_entropy(token) >= threshold:
            findings.append(
                TextFinding(
                    rule_id=rule.id,
                    family=rule.family,
                    category=rule.category,
                    severity=rule.severity,
                    weight=rule.weight,
                    evidence=_extract_evidence(text, match.start(), match.end()),
                    match_start=match.start(),
                    match_end=match.end(),
                )
            )
    return findings


def scan_text(text: str, rule_set: RuleSet) -> TextScanResult:
    all_findings: list[TextFinding] = []
    scanners = {
        "regex": _scan_regex_rule,
        "keyword": _scan_keyword_rule,
        "entropy": _scan_entropy_rule,
    }
    for rule in rule_set.text_scan_rules:
        if not rule.enabled:
            continue
        scanner = scanners.get(rule.category)
        if scanner is None:
            continue
        all_findings.extend(scanner(text, rule))

    enabled_weight_total = sum(r.weight for r in rule_set.text_scan_rules if r.enabled)
    matched_rule_ids = {f.rule_id for f in all_findings}
    matched_weight = sum(
        r.weight for r in rule_set.text_scan_rules if r.id in matched_rule_ids and r.enabled
    )
    total_score = (
        round(min((matched_weight / enabled_weight_total) * 100.0, 100.0), 2)
        if enabled_weight_total > 0
        else 0.0
    )
    return TextScanResult(
        findings=all_findings,
        total_score=total_score,
        matched_count=len(all_findings),
    )


def text_scan_rule_matches(txt_result: TextScanResult, rule_set: RuleSet) -> list[RuleMatch]:
    matched_ids = {f.rule_id for f in txt_result.findings}
    return [
        RuleMatch(
            rule_name=rule.id,
            severity=rule.severity,
            weight=rule.weight,
            matched=rule.id in matched_ids,
        )
        for rule in rule_set.text_scan_rules
        if rule.enabled
    ]


# ── Locked deterministic scoring model (forked from Valo) ─────────────────────

_SEV_BASE: dict[int, float] = {5: 80.0, 4: 60.0, 3: 40.0, 2: 20.0, 1: 10.0}
_BREADTH_MAP: dict[int, float] = {0: 0.0, 1: 0.0, 2: 5.0, 3: 10.0}
_REPETITION_TIERS: list[tuple[int, float]] = [(10, 10.0), (7, 8.0), (4, 6.0), (2, 3.0)]


def _breadth_bonus(distinct_families: int) -> float:
    if distinct_families >= 4:
        return 15.0
    return _BREADTH_MAP.get(distinct_families, 0.0)


def _repetition_bonus(total_triggers: int) -> float:
    for threshold, bonus in _REPETITION_TIERS:
        if total_triggers >= threshold:
            return bonus
    return 0.0


def cvss_combined_score(
    context_score: float,
    findings: list[TextFinding],
    text_scan_rules: list[TextScanRule],
) -> float:
    """min(100, base_severity + breadth_bonus + repetition_bonus). Deterministic."""
    if not findings:
        return round(min(100.0, context_score * 0.5), 2)

    rule_map = {r.id: r for r in text_scan_rules}
    severities = [rule_map[f.rule_id].severity for f in findings if f.rule_id in rule_map]
    max_sev = max(severities) if severities else 1
    base = _SEV_BASE.get(max_sev, 10.0)
    families = {
        rule_map[f.rule_id].family
        for f in findings
        if f.rule_id in rule_map and rule_map[f.rule_id].family
    }
    breadth = _breadth_bonus(len(families))
    repetition = _repetition_bonus(len(findings))
    return round(min(100.0, base + breadth + repetition), 2)


def severity_info(findings: list[TextFinding]) -> tuple[int, bool]:
    if not findings:
        return 0, False
    max_sev = max(f.severity for f in findings)
    return max_sev, max_sev >= 4
