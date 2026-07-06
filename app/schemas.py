"""Pydantic data models for AgentShadow.

The rule-engine and policy-engine models (Pattern, Rule, TextScanRule,
TextFinding, RuleMatch, Policy, ...) are forked verbatim from Valo so the
deterministic engine logic is reused unchanged. The Agent* models are
AgentShadow-specific: an AI agent is the asset type being inventoried.
"""

import re
import uuid
from datetime import datetime, timezone
from typing import Any, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


# ── Rule engine models (forked from Valo) ────────────────────────────────────

PatternOp = Literal[
    "eq", "neq", "in", "not_in", "contains", "not_contains",
    "gte", "lte", "gt", "lt", "matches", "exists", "not_exists",
]


class Pattern(BaseModel):
    model_config = ConfigDict(extra="ignore")
    field: str = Field(min_length=1)
    op: PatternOp
    value: Any | None = Field(default=None)


class Rule(BaseModel):
    model_config = ConfigDict(extra="ignore")
    name: str = Field(min_length=1)
    severity: int = Field(ge=1, le=5)
    weight: float = Field(gt=0)
    enabled: bool = True
    patterns: List[Pattern] = Field(default_factory=list)


TextScanRuleCategory = Literal["regex", "keyword", "entropy"]


class TextScanRule(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(min_length=1)
    family: Optional[str] = Field(default=None)
    category: TextScanRuleCategory
    pattern: str = Field(default="")
    severity: int = Field(ge=1, le=5)
    weight: float = Field(gt=0)
    enabled: bool = True
    description: Optional[str] = Field(default=None)

    @model_validator(mode="after")
    def _validate_pattern_for_category(self) -> "TextScanRule":
        if self.category in ("regex", "keyword") and not self.pattern:
            raise ValueError(
                f"Rule '{self.id}': 'pattern' must not be empty for category '{self.category}'"
            )
        return self


class TextFinding(BaseModel):
    rule_id: str
    family: Optional[str] = None
    category: str
    severity: int = Field(ge=1, le=5)
    weight: float
    evidence: str
    match_start: Optional[int] = None
    match_end: Optional[int] = None


class TextScanResult(BaseModel):
    findings: List[TextFinding] = Field(default_factory=list)
    total_score: float = Field(default=0.0, ge=0)
    matched_count: int = Field(default=0, ge=0)


class RuleMatch(BaseModel):
    rule_name: str
    severity: int
    weight: float
    matched: bool


class RuleEngineResult(BaseModel):
    matched_rules: List[RuleMatch] = Field(default_factory=list)
    total_score: float = Field(default=0.0, ge=0)
    passed_count: int = Field(default=0, ge=0)
    failed_count: int = Field(default=0, ge=0)


class RuleSet(BaseModel):
    rules: List[Rule] = Field(default_factory=list)
    text_scan_rules: List[TextScanRule] = Field(default_factory=list)


# ── Policy engine models (forked from Valo) ──────────────────────────────────

PolicyConditionOp = Literal[
    "eq", "ne", "gt", "gte", "lt", "lte", "in", "not_in",
    "contains", "matches", "exists", "not_exists",
]

PolicyDecisionLiteral = Literal["allow", "warn", "deny"]


class PolicyCondition(BaseModel):
    model_config = ConfigDict(extra="forbid")
    field: str = Field(min_length=1)
    op: PolicyConditionOp
    value: Any | None = Field(default=None)


class PolicyAction(BaseModel):
    model_config = ConfigDict(extra="forbid")
    decision: PolicyDecisionLiteral
    severity: int = Field(ge=0, le=10, default=5)
    message: str = Field(min_length=1)


class Policy(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str = Field(min_length=1, max_length=80)
    name: str = Field(min_length=1)
    description: Optional[str] = None
    enabled: bool = True
    enforce: bool = True
    when: List[PolicyCondition] = Field(default_factory=list)
    then: PolicyAction
    tags: List[str] = Field(default_factory=list)
    version: int = Field(default=1, ge=1)
    updated_at: Optional[datetime] = None

    @field_validator("id")
    @classmethod
    def _validate_id(cls, value: str) -> str:
        slug = str(value or "").strip()
        if not slug or not re.match(r"^[a-zA-Z0-9_\-]+$", slug):
            raise ValueError("Policy id must contain only letters, digits, '_' or '-'")
        return slug


class PolicySet(BaseModel):
    policies: List[Policy] = Field(default_factory=list)


class PolicyDecision(BaseModel):
    policy_id: str
    name: str
    matched: bool
    decision: PolicyDecisionLiteral
    severity: int = Field(ge=0, le=10)
    message: str
    reasons: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)


# ── Agent inventory models (AgentShadow-specific) ────────────────────────────

AgentSource = Literal["code", "runtime"]
AutonomyLevel = Literal["low", "medium", "high", "unknown"]
RiskLevel = Literal["CRITICAL", "HIGH", "MEDIUM", "LOW", "MINIMAL"]


class AgentProfile(BaseModel):
    """Raw, framework-agnostic description of a discovered agent.

    Built by either the code scanner (from detected framework usage) or a
    runtime connector (from a live agent definition). This is the input that
    gets scored by the pipeline.
    """

    name: str = Field(min_length=1)
    framework: str = Field(default="unknown")
    source: AgentSource = "code"
    owner: str = Field(default="unassigned")
    discovery_path: str = Field(default="", description="File path or runtime endpoint")
    model: Optional[str] = Field(default=None)
    system_prompt: Optional[str] = Field(default=None)
    tools: List[str] = Field(default_factory=list)
    autonomy_level: AutonomyLevel = "unknown"
    evidence: List[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    def agent_id(self) -> str:
        slug = re.sub(r"[^a-zA-Z0-9_.-]+", "-", self.name).strip("-").lower() or "agent"
        owner = re.sub(r"[^a-zA-Z0-9_.-]+", "-", self.owner).strip("-").lower() or "unassigned"
        return f"agent://{owner}/{slug}"


class Agent(BaseModel):
    """A scored, persisted agent record as stored in the inventory."""

    agent_id: str
    name: str
    framework: str = "unknown"
    source: AgentSource = "code"
    owner: str = "unassigned"
    discovery_path: str = ""
    model: Optional[str] = None
    autonomy_level: AutonomyLevel = "unknown"
    tools: List[str] = Field(default_factory=list)
    tool_count: int = 0
    risk_score: float = Field(default=0.0, ge=0, le=100)
    risk_level: RiskLevel = "MINIMAL"
    max_severity: int = Field(default=0, ge=0, le=5)
    posture_grade: str = "A"
    final_decision: PolicyDecisionLiteral = "allow"
    finding_count: int = 0
    findings: List[TextFinding] = Field(default_factory=list)
    policy_decisions: List[PolicyDecision] = Field(default_factory=list)
    first_seen: datetime = Field(default_factory=_utcnow)
    last_seen: datetime = Field(default_factory=_utcnow)
    scan_count: int = 1
    metadata: dict[str, Any] = Field(default_factory=dict)


# ── API request / response models ────────────────────────────────────────────


class ReportBranding(BaseModel):
    company_name: Optional[str] = None
    logo_base64: Optional[str] = None
    prepared_by: Optional[str] = None
    reviewed_by: Optional[str] = None
    distribution: Optional[str] = None


class RepositoryScanRequest(BaseModel):
    path: str = Field(min_length=1, description="Absolute or relative path to a code repository")
    owner: str = Field(default="unassigned", description="Team/owner attributed to discovered agents")


class ConnectorSyncRequest(BaseModel):
    model_config = ConfigDict(extra="ignore")
    owner: str = Field(default="unassigned")
    options: dict[str, Any] = Field(default_factory=dict)


class ScanSummary(BaseModel):
    discovered: int = Field(default=0, ge=0)
    new_agents: int = Field(default=0, ge=0)
    updated_agents: int = Field(default=0, ge=0)
    agents: List[Agent] = Field(default_factory=list)
    source: AgentSource = "code"
    detail: str = ""


class AgentListResponse(BaseModel):
    total: int = Field(ge=0)
    returned: int = Field(ge=0)
    agents: List[Agent] = Field(default_factory=list)


class FrameworkCount(BaseModel):
    framework: str
    count: int = Field(ge=0)
    avg_risk: float = Field(default=0.0, ge=0)


class RiskDistribution(BaseModel):
    critical: int = 0
    high: int = 0
    medium: int = 0
    low: int = 0
    minimal: int = 0


class DashboardOverview(BaseModel):
    generated_at: datetime = Field(default_factory=_utcnow)
    total_agents: int = Field(default=0, ge=0)
    high_risk_agents: int = Field(default=0, ge=0)
    unmanaged_agents: int = Field(default=0, ge=0)
    high_autonomy_agents: int = Field(default=0, ge=0)
    average_risk_score: float = Field(default=0.0, ge=0)
    by_framework: List[FrameworkCount] = Field(default_factory=list)
    by_source: dict[str, int] = Field(default_factory=dict)
    risk_distribution: RiskDistribution = Field(default_factory=RiskDistribution)
    policy_breaches: int = Field(default=0, ge=0)


class ConnectorInfo(BaseModel):
    id: str
    name: str
    description: str
    category: str


class HealthResponse(BaseModel):
    status: str = "ok"
    service: str = "AgentShadow"
    version: str = "0.1.0"
