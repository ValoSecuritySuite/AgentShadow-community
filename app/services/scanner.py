"""Code-based agent discovery.

Walks a repository, runs the agent-framework detector on each source file, and
turns every file that uses an agent framework into a scored agent. Also parses
dependency manifests for known agent packages (manifest-level signal, mirroring
LLMShadow's dependency scanning).
"""

from pathlib import Path

from app.core.logging import get_logger
from app.detectors.agent_frameworks import (
    KNOWN_AGENT_PACKAGES,
    detect_file,
    estimate_autonomy,
)
from app.schemas import Agent, AgentProfile
from app.services import inventory_store
from app.services.pipeline import score_agent
from app.services.rules_loader import load_rules

logger = get_logger(__name__)

_SCANNABLE_SUFFIXES = {".py", ".ipynb", ".ts", ".tsx", ".js", ".jsx", ".yaml", ".yml", ".toml", ".json"}
_SKIP_DIRS = {".git", "node_modules", ".venv", "venv", "__pycache__", "dist", "build", ".next"}
_MAX_FILE_BYTES = 1_000_000


def _iter_files(root: Path):
    for path in root.rglob("*"):
        if path.is_dir():
            continue
        if any(part in _SKIP_DIRS for part in path.parts):
            continue
        if path.suffix.lower() not in _SCANNABLE_SUFFIXES:
            continue
        try:
            if path.stat().st_size > _MAX_FILE_BYTES:
                continue
        except OSError:
            continue
        yield path


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return ""


def _display_name(file_stem: str, content: str) -> str:
    """Prefer the first line of the module docstring as the agent display name."""
    import re

    match = re.match(r'^[\s\r\n]*(?:"""|\'\'\')(.*?)(?:\n|"""|\'\'\')', content, re.DOTALL)
    if match:
        first_line = match.group(1).strip().splitlines()[0].strip().rstrip(".")
        if first_line:
            return first_line
    return file_stem.replace("_", " ").replace("-", " ").title()


def scan_repository(repo_path: str, owner: str = "unassigned") -> list[Agent]:
    """Scan a repository directory and return scored agents (also persisted)."""
    root = Path(repo_path).expanduser().resolve()
    if not root.exists() or not root.is_dir():
        raise FileNotFoundError(f"Repository path not found or not a directory: {repo_path}")

    rules = load_rules()
    repo_name = root.name
    scored: list[Agent] = []

    for file_path in _iter_files(root):
        content = _read(file_path)
        if not content:
            continue
        detection = detect_file(str(file_path), content)
        if not detection.is_agent:
            continue

        rel = file_path.relative_to(root)
        primary_framework = sorted(detection.frameworks)[0]
        agent_name = _display_name(rel.stem, content)
        evidence = [f"{h.framework} @ L{h.line}: {h.evidence}" for h in detection.hits[:12]]

        profile = AgentProfile(
            name=agent_name,
            framework=primary_framework,
            source="code",
            owner=owner,
            discovery_path=str(file_path),
            tools=sorted(detection.tools),
            autonomy_level=estimate_autonomy(detection.tools),
            evidence=evidence,
            system_prompt=_extract_snippet(content),
            metadata={
                "repository": repo_name,
                "relative_path": rel.as_posix(),
                "frameworks": sorted(detection.frameworks),
            },
        )
        agent = score_agent(profile, rules)
        inventory_store.upsert_agent(agent)
        scored.append(agent)

    logger.info("Repository scan of %s discovered %d agents", repo_name, len(scored))
    return scored


def _extract_snippet(content: str, max_chars: int = 1500) -> str:
    """Return a representative leading slice of the file as the scannable surface."""
    return content[:max_chars]


def parse_dependency_manifests(repo_path: str) -> dict[str, str]:
    """Return {package: framework} for known agent packages found in manifests."""
    root = Path(repo_path).expanduser().resolve()
    found: dict[str, str] = {}
    for manifest in ("requirements.txt", "pyproject.toml", "package.json"):
        p = root / manifest
        if not p.exists():
            continue
        text = _read(p).lower()
        for pkg, framework in KNOWN_AGENT_PACKAGES.items():
            if pkg.lower() in text:
                found[pkg] = framework
    return found
