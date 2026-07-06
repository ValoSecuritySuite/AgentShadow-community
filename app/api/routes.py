"""AgentShadow REST API."""

from typing import Optional

from fastapi import APIRouter, HTTPException, Query, Response

from app.core.edition import edition_meta, require_pro
from app.core.logging import get_logger
from app.connectors import registry
from app.schemas import (
    Agent,
    AgentListResponse,
    ConnectorSyncRequest,
    DashboardOverview,
    HealthResponse,
    Policy,
    RepositoryScanRequest,
    ReportBranding,
    ScanSummary,
)
from app.services import dashboard, inventory_store, scanner
from app.services.correlation_emitter import emit_agents
from app.services.pdf_report import generate_agent_report
from app.services.policy_store import clear_policies_cache, load_policies
from app.services.rules_loader import clear_rules_cache, load_rules

logger = get_logger(__name__)
router = APIRouter()


@router.get("/health", response_model=HealthResponse, tags=["system"])
def health() -> HealthResponse:
    return HealthResponse()


@router.get("/meta", tags=["system"])
def meta() -> dict:
    """Edition metadata: which features are free vs. locked behind an upgrade."""
    return edition_meta()


# ── Discovery ────────────────────────────────────────────────────────────────


@router.post("/scan/repository", response_model=ScanSummary, tags=["discovery"])
def scan_repository(req: RepositoryScanRequest) -> ScanSummary:
    try:
        before = {a.agent_id for a in inventory_store.list_agents()}
        agents = scanner.scan_repository(req.path, owner=req.owner)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    emit_agents(agents)
    new = [a for a in agents if a.agent_id not in before]
    return ScanSummary(
        discovered=len(agents),
        new_agents=len(new),
        updated_agents=len(agents) - len(new),
        agents=agents,
        source="code",
        detail=f"Scanned repository '{req.path}'",
    )


@router.get("/connectors", tags=["discovery"])
def list_connectors() -> dict:
    return {"connectors": [c.model_dump() for c in registry.list_connectors()]}


@router.post("/connectors/{connector_id}/sync", response_model=ScanSummary, tags=["discovery"])
def sync_connector(connector_id: str, req: ConnectorSyncRequest) -> ScanSummary:
    require_pro("runtime_connectors")
    try:
        before = {a.agent_id for a in inventory_store.list_agents()}
        agents = registry.sync_connector(connector_id, owner=req.owner, options=req.options)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=f"Unknown connector '{connector_id}'") from exc
    emit_agents(agents)
    new = [a for a in agents if a.agent_id not in before]
    return ScanSummary(
        discovered=len(agents),
        new_agents=len(new),
        updated_agents=len(agents) - len(new),
        agents=agents,
        source="runtime",
        detail=f"Synced connector '{connector_id}'",
    )


# ── Inventory ────────────────────────────────────────────────────────────────


@router.get("/agents/discovered", response_model=AgentListResponse, tags=["inventory"])
def discovered_agents(
    framework: Optional[str] = Query(default=None),
    source: Optional[str] = Query(default=None),
    risk_level: Optional[str] = Query(default=None),
    owner: Optional[str] = Query(default=None),
) -> AgentListResponse:
    agents = inventory_store.list_agents(
        framework=framework, source=source, risk_level=risk_level, owner=owner
    )
    return AgentListResponse(total=len(agents), returned=len(agents), agents=agents)


@router.get("/agents/detail", response_model=Agent, tags=["inventory"])
def agent_detail(agent_id: str = Query(...)) -> Agent:
    agent = inventory_store.get_agent(agent_id)
    if agent is None:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_id}' not found")
    return agent


# ── Executive dashboard ──────────────────────────────────────────────────────


@router.get("/dashboard/overview", response_model=DashboardOverview, tags=["dashboard"])
def dashboard_overview() -> DashboardOverview:
    return dashboard.compute_overview()


# ── Reporting ────────────────────────────────────────────────────────────────


@router.post("/report/pdf", tags=["reporting"])
def report_pdf(
    agent_id: str = Query(...),
    branding: Optional[ReportBranding] = None,
) -> Response:
    require_pro("pdf_reports")
    agent = inventory_store.get_agent(agent_id)
    if agent is None:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_id}' not found")
    pdf_bytes = generate_agent_report(agent, branding)
    safe_name = agent.name.replace("/", "_").replace(":", "_")
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="AgentShadow_{safe_name}.pdf"'},
    )


# ── Governance / policies ────────────────────────────────────────────────────


@router.get("/policies", tags=["governance"])
def list_policies() -> dict:
    policy_set = load_policies()
    return {
        "total": len(policy_set.policies),
        "policies": [p.model_dump(mode="json") for p in policy_set.policies],
    }


@router.post("/policies/reload", tags=["governance"])
def reload_policies() -> dict:
    clear_policies_cache()
    policy_set = load_policies(force=True)
    return {"reloaded": True, "policy_count": len(policy_set.policies)}


@router.post("/rules/reload", tags=["governance"])
def reload_rules() -> dict:
    clear_rules_cache()
    rule_set = load_rules(force=True)
    return {
        "reloaded": True,
        "context_rule_count": len(rule_set.rules),
        "text_scan_rule_count": len(rule_set.text_scan_rules),
    }


# ── Admin ────────────────────────────────────────────────────────────────────


@router.post("/admin/reset", tags=["system"])
def reset_inventory() -> dict:
    removed = inventory_store.clear_all()
    return {"cleared": removed}
