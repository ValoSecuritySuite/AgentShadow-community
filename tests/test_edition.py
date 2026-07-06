"""Community Edition gating: locked endpoints, /meta, and Pro override."""

from .conftest import SAMPLE_AGENTS_DIR


def test_meta_reports_community(client):
    resp = client.get("/meta")
    assert resp.status_code == 200
    body = resp.json()
    assert body["edition"] == "community"
    assert body["is_community"] is True
    assert "runtime_connectors" in body["locked_features"]
    assert "pdf_reports" in body["locked_features"]
    assert body["upgrade_url"]


def test_runtime_connector_locked_in_community(client):
    resp = client.post("/connectors/openai_assistants/sync", json={"owner": "ops"})
    assert resp.status_code == 402
    detail = resp.json()["detail"]
    assert detail["error"] == "upgrade_required"
    assert detail["feature"] == "runtime_connectors"
    assert detail["tier"] == "Pro"


def test_connectors_listing_stays_open_in_community(client):
    # The list endpoint stays available so the UI can show connectors as locked.
    resp = client.get("/connectors")
    assert resp.status_code == 200
    assert any(c["id"] == "openai_assistants" for c in resp.json()["connectors"])


def test_pdf_locked_in_community(client):
    client.post("/scan/repository", json={"path": SAMPLE_AGENTS_DIR, "owner": "x"})
    agents = client.get("/agents/discovered").json()["agents"]
    assert agents, "expected the sample repo scan to discover at least one agent"
    resp = client.post("/report/pdf", params={"agent_id": agents[0]["agent_id"]})
    assert resp.status_code == 402
    assert resp.json()["detail"]["feature"] == "pdf_reports"


def test_code_scan_is_free_in_community(client):
    resp = client.post("/scan/repository", json={"path": SAMPLE_AGENTS_DIR, "owner": "x"})
    assert resp.status_code == 200
    assert resp.json()["discovered"] >= 1


def test_pro_edition_unlocks_runtime_and_pdf(client, pro_edition):
    assert client.get("/meta").json()["edition"] == "pro"

    sync = client.post("/connectors/openai_assistants/sync", json={"owner": "ops"})
    assert sync.status_code == 200
    agent_id = sync.json()["agents"][0]["agent_id"]

    pdf = client.post("/report/pdf", params={"agent_id": agent_id})
    assert pdf.status_code == 200
    assert pdf.content[:4] == b"%PDF"
