"""Executive dashboard metrics computed from the agent inventory."""

from collections import defaultdict

from app.schemas import (
    Agent,
    DashboardOverview,
    FrameworkCount,
    RiskDistribution,
)
from app.services import inventory_store


def compute_overview() -> DashboardOverview:
    agents: list[Agent] = inventory_store.list_agents()
    total = len(agents)

    dist = RiskDistribution()
    by_framework_count: dict[str, int] = defaultdict(int)
    by_framework_risk: dict[str, float] = defaultdict(float)
    by_source: dict[str, int] = defaultdict(int)
    high_risk = 0
    unmanaged = 0
    high_autonomy = 0
    breaches = 0
    score_total = 0.0

    for agent in agents:
        score_total += agent.risk_score
        level = agent.risk_level.lower()
        if hasattr(dist, level):
            setattr(dist, level, getattr(dist, level) + 1)
        if agent.risk_score >= 60:
            high_risk += 1
        if agent.owner == "unassigned":
            unmanaged += 1
        if agent.autonomy_level == "high":
            high_autonomy += 1
        if agent.final_decision in ("warn", "deny"):
            breaches += 1
        by_framework_count[agent.framework] += 1
        by_framework_risk[agent.framework] += agent.risk_score
        by_source[agent.source] += 1

    by_framework = [
        FrameworkCount(
            framework=fw,
            count=count,
            avg_risk=round(by_framework_risk[fw] / count, 2) if count else 0.0,
        )
        for fw, count in sorted(by_framework_count.items(), key=lambda kv: kv[1], reverse=True)
    ]

    return DashboardOverview(
        total_agents=total,
        high_risk_agents=high_risk,
        unmanaged_agents=unmanaged,
        high_autonomy_agents=high_autonomy,
        average_risk_score=round(score_total / total, 2) if total else 0.0,
        by_framework=by_framework,
        by_source=dict(by_source),
        risk_distribution=dist,
        policy_breaches=breaches,
    )
