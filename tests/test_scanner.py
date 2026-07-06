"""Code scanner discovers agents in the bundled sample repository."""

import pytest

from app.services import scanner

from .conftest import SAMPLE_AGENTS_DIR


def test_scan_sample_repository_finds_agents():
    agents = scanner.scan_repository(SAMPLE_AGENTS_DIR, owner="research")
    assert len(agents) >= 1
    assert all(a.source == "code" for a in agents)
    assert all(a.owner == "research" for a in agents)
    # Every discovered agent should carry a deterministic risk band.
    assert all(a.risk_level in {"CRITICAL", "HIGH", "MEDIUM", "LOW", "MINIMAL"} for a in agents)


def test_scan_missing_path_raises():
    with pytest.raises(FileNotFoundError):
        scanner.scan_repository("/nonexistent/path/xyz", owner="nobody")


def test_dependency_manifest_parsing(tmp_path):
    (tmp_path / "requirements.txt").write_text("langchain==0.2.0\ncrewai\nrequests\n")
    found = scanner.parse_dependency_manifests(str(tmp_path))
    assert "langchain" in found
