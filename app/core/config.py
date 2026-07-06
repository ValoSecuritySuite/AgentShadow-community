"""Runtime configuration for AgentShadow.

Mirrors the lightweight env-driven config pattern used across the Valo
ecosystem (APP_* prefixed variables) so AgentShadow can be deployed
alongside the existing services with no surprises.
"""

import os
from functools import lru_cache
from pathlib import Path

_APP_DIR = Path(__file__).resolve().parent.parent
_BASE_DIR = _APP_DIR.parent


def _env_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _env_str(name: str, default: str) -> str:
    value = os.getenv(name)
    return value if value is not None and value != "" else default


def _env_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


class Settings:
    """Process-wide settings, resolved once from the environment."""

    def __init__(self) -> None:
        self.app_name: str = "AgentShadow"
        self.log_level: str = _env_str("APP_LOG_LEVEL", "INFO").upper()

        # Detection + governance content
        self.rules_path: str = _env_str(
            "APP_RULES_PATH", str(_APP_DIR / "rules" / "agentshadow_rules.yml")
        )
        self.policies_path: str = _env_str(
            "APP_POLICIES_PATH", str(_APP_DIR / "policies" / "governance")
        )
        self.rules_cache_ttl_seconds: int = _env_int("APP_RULES_CACHE_TTL_SECONDS", 30)

        # Inventory persistence
        self.inventory_db_path: str = _env_str(
            "APP_INVENTORY_DB_PATH", str(_BASE_DIR / "data" / "agentshadow.db")
        )

        # CORS
        self.cors_allowed_origins: list[str] = self._parse_origins(
            _env_str("APP_CORS_ALLOWED_ORIGINS", "*")
        )

        # Access control. When one or more API keys are configured the API is
        # locked down (everything except the liveness probe requires a valid
        # `X-API-Key` header). With no keys set, auth is disabled so local dev
        # and the demo keep working out of the box.
        self.api_keys: list[str] = self._parse_api_keys(
            _env_str("APP_API_KEYS", _env_str("APP_API_KEY", ""))
        )
        # Allow explicitly disabling auth even when keys are present (handy for
        # tests / temporary local debugging).
        self._auth_disabled_override: bool = not _env_bool("APP_AUTH_ENABLED", True)

        # Correlation engine integration (the shared cross-tool asset graph)
        self.correlation_enabled: bool = _env_bool("APP_CORRELATION_ENGINE_ENABLED", False)
        self.correlation_url: str = _env_str(
            "APP_CORRELATION_ENGINE_URL", "http://correlation:8100"
        )
        self.correlation_secret: str = _env_str(
            "APP_CORRELATION_ENGINE_SECRET", "agentshadow-shared-dev-secret"
        )
        self.correlation_source_slug: str = _env_str(
            "APP_CORRELATION_SOURCE_SLUG", "agentshadow"
        )

    @property
    def auth_enabled(self) -> bool:
        """Auth is active only when keys are configured and not overridden off."""
        return bool(self.api_keys) and not self._auth_disabled_override

    @staticmethod
    def _parse_api_keys(raw: str) -> list[str]:
        raw = (raw or "").strip()
        if not raw:
            return []
        if raw.startswith("["):
            import json

            try:
                parsed = json.loads(raw)
                if isinstance(parsed, list):
                    return [str(item).strip() for item in parsed if str(item).strip()]
            except json.JSONDecodeError:
                pass
        return [item.strip() for item in raw.split(",") if item.strip()]

    @staticmethod
    def _parse_origins(raw: str) -> list[str]:
        raw = raw.strip()
        if raw in {"", "*"}:
            return ["*"]
        if raw.startswith("["):
            import json

            try:
                parsed = json.loads(raw)
                if isinstance(parsed, list):
                    return [str(item) for item in parsed]
            except json.JSONDecodeError:
                pass
        return [item.strip() for item in raw.split(",") if item.strip()]


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
