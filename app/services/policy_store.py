"""Load governance policies from a directory of YAML files (one per policy)."""

import time
from pathlib import Path

import yaml

from app.core.config import get_settings
from app.core.logging import get_logger
from app.schemas import Policy, PolicySet

logger = get_logger(__name__)

_cache: tuple[float, PolicySet] | None = None


def load_policies(*, force: bool = False) -> PolicySet:
    global _cache
    settings = get_settings()
    now = time.time()

    if not force and _cache is not None:
        cached_at, policy_set = _cache
        if now - cached_at < settings.rules_cache_ttl_seconds:
            return policy_set

    directory = Path(settings.policies_path)
    policies: list[Policy] = []
    if directory.exists():
        for yml in sorted(directory.glob("*.yml")):
            try:
                data = yaml.safe_load(yml.read_text(encoding="utf-8")) or {}
                policies.append(Policy.model_validate(data))
            except Exception as exc:  # noqa: BLE001 - skip malformed policy, keep serving
                logger.warning("Skipping invalid policy %s: %s", yml.name, exc)
    else:
        logger.warning("Policies directory not found at %s", directory)

    policy_set = PolicySet(policies=policies)
    logger.info("Loaded %d governance policies", len(policies))
    _cache = (now, policy_set)
    return policy_set


def clear_policies_cache() -> None:
    global _cache
    _cache = None
