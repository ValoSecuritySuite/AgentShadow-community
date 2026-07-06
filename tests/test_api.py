"""End-to-end API behaviour via FastAPI's TestClient (auth disabled)."""

from .conftest import SAMPLE_AGENTS_DIR


def test_health_ok(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["service"] == "AgentShadow"


def test_scan_then_inventory_and_dashboard(client):
    scan = client.post("/scan/repository", json={"path": SAMPLE_AGENTS_DIR, "owner": "research"})
    assert scan.status_code == 200
    summary = scan.json()
    assert summary["discovered"] >= 1
    assert summary["source"] == "code"

    listing = client.get("/agents/discovered")
    assert listing.status_code == 200
    agents = listing.json()["agents"]
    assert len(agents) == summary["discovered"]

    overview = client.get("/dashboard/overview")
    assert overview.status_code == 200
    assert overview.json()["total_agents"] == len(agents)


def test_scan_missing_path_returns_404(client):
    resp = client.post("/scan/repository", json={"path": "/no/such/repo", "owner": "x"})
    assert resp.status_code == 404


def test_connector_sync_and_detail_and_pdf(client, pro_edition):
    connectors = client.get("/connectors").json()["connectors"]
    assert any(c["id"] == "openai_assistants" for c in connectors)

    sync = client.post("/connectors/openai_assistants/sync", json={"owner": "ops"})
    assert sync.status_code == 200
    agents = sync.json()["agents"]
    assert len(agents) >= 1

    agent_id = agents[0]["agent_id"]
    detail = client.get("/agents/detail", params={"agent_id": agent_id})
    assert detail.status_code == 200
    assert detail.json()["agent_id"] == agent_id

    pdf = client.post("/report/pdf", params={"agent_id": agent_id})
    assert pdf.status_code == 200
    assert pdf.headers["content-type"] == "application/pdf"
    assert pdf.content[:4] == b"%PDF"


def test_unknown_connector_returns_404(client, pro_edition):
    resp = client.post("/connectors/does_not_exist/sync", json={"owner": "ops"})
    assert resp.status_code == 404


def test_detail_unknown_agent_returns_404(client):
    resp = client.get("/agents/detail", params={"agent_id": "agent://nobody/ghost"})
    assert resp.status_code == 404


def test_policies_listing(client):
    resp = client.get("/policies")
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] >= 1
    assert isinstance(body["policies"], list)
