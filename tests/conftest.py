"""Shared pytest fixtures for AgentShadow.

The inventory store is SQLite-backed, so every test run is pointed at a throwaway
database via `APP_INVENTORY_DB_PATH` (set *before* the app config is first
resolved). Auth is left disabled by default; the auth tests opt in explicitly.
"""

import os
import tempfile

# Must be set before app.core.config.get_settings() is first cached.
_TMP_DIR = tempfile.mkdtemp(prefix="agentshadow-test-")
os.environ["APP_INVENTORY_DB_PATH"] = os.path.join(_TMP_DIR, "inventory.db")
os.environ.setdefault("APP_AUTH_ENABLED", "true")
os.environ.pop("APP_API_KEY", None)
os.environ.pop("APP_API_KEYS", None)
os.environ.pop("OPENAI_API_KEY", None)
# Default to the Community Edition so gating is exercised; premium tests opt in.
os.environ.pop("APP_EDITION", None)

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.core.config import get_settings  # noqa: E402
from app.core.edition import get_edition  # noqa: E402
from app.main import app  # noqa: E402
from app.services import inventory_store  # noqa: E402

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SAMPLE_AGENTS_DIR = os.path.join(REPO_ROOT, "sample_agents")


@pytest.fixture(autouse=True)
def _clean_inventory():
    """Start every test from an empty inventory."""
    inventory_store.init_db()
    inventory_store.clear_all()
    yield
    inventory_store.clear_all()


@pytest.fixture()
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture()
def enable_auth(monkeypatch):
    """Enable API-key auth for the duration of a test."""
    key = "test-secret-key"
    monkeypatch.setenv("APP_API_KEYS", key)
    get_settings.cache_clear()
    yield key
    monkeypatch.delenv("APP_API_KEYS", raising=False)
    get_settings.cache_clear()


@pytest.fixture()
def pro_edition(monkeypatch):
    """Unlock premium features by running as the Pro edition for a test."""
    monkeypatch.setenv("APP_EDITION", "pro")
    get_edition.cache_clear()
    yield
    monkeypatch.delenv("APP_EDITION", raising=False)
    get_edition.cache_clear()
