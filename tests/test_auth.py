"""API-key access control."""


def test_auth_disabled_by_default(client):
    # No keys configured -> protected endpoints are open.
    assert client.get("/dashboard/overview").status_code == 200


def test_protected_endpoint_requires_key_when_enabled(client, enable_auth):
    resp = client.get("/dashboard/overview")
    assert resp.status_code == 401


def test_valid_key_grants_access(client, enable_auth):
    resp = client.get("/dashboard/overview", headers={"X-API-Key": enable_auth})
    assert resp.status_code == 200


def test_invalid_key_rejected(client, enable_auth):
    resp = client.get("/dashboard/overview", headers={"X-API-Key": "wrong-key"})
    assert resp.status_code == 401


def test_health_stays_open_even_with_auth(client, enable_auth):
    # The container healthcheck hits /health without a key.
    assert client.get("/health").status_code == 200


def test_write_endpoint_blocked_without_key(client, enable_auth, pro_edition):
    resp = client.post("/connectors/openai_assistants/sync", json={"owner": "ops"})
    assert resp.status_code == 401

    ok = client.post(
        "/connectors/openai_assistants/sync",
        json={"owner": "ops"},
        headers={"X-API-Key": enable_auth},
    )
    assert ok.status_code == 200
