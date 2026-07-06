"""YAML rules loader with a small TTL cache (forked from Valo/LLMShadow)."""

import time
from pathlib import Path

import yaml

from app.core.config import get_settings
from app.core.logging import get_logger
from app.schemas import RuleSet

logger = get_logger(__name__)

_cache: dict[str, tuple[float, RuleSet]] = {}


def load_rules(path: str | None = None, *, force: bool = False) -> RuleSet:
    settings = get_settings()
    rules_path = path or settings.rules_path
    now = time.time()

    if not force and rules_path in _cache:
        cached_at, ruleset = _cache[rules_path]
        if now - cached_at < settings.rules_cache_ttl_seconds:
            return ruleset

    file_path = Path(rules_path)
    if not file_path.exists():
        logger.warning("Rules file not found at %s; using empty rule set", rules_path)
        ruleset = RuleSet()
    else:
        data = yaml.safe_load(file_path.read_text(encoding="utf-8")) or {}
        ruleset = RuleSet.model_validate(data)
        logger.info(
            "Loaded %d context rules + %d text-scan rules from %s",
            len(ruleset.rules),
            len(ruleset.text_scan_rules),
            file_path.name,
        )

    _cache[rules_path] = (now, ruleset)
    return ruleset


def clear_rules_cache() -> None:
    _cache.clear()
