"""API access control for AgentShadow.

A lightweight, demo-friendly API-key gate. When one or more keys are configured
(`APP_API_KEYS` / `APP_API_KEY`), every endpoint except the liveness probe
requires a matching `X-API-Key` header. With no keys configured the gate is a
no-op so local development and the demo keep working without credentials.

Key comparison uses `hmac.compare_digest` to avoid timing side-channels — the
same hardening the rest of the Valo ecosystem applies to shared secrets.
"""

import hmac

from fastapi import HTTPException, Request, Security, status
from fastapi.security import APIKeyHeader

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)

API_KEY_HEADER_NAME = "X-API-Key"

# Paths that must stay reachable without a key (container healthcheck, schema).
_EXEMPT_PATHS = {"/health", "/docs", "/redoc", "/openapi.json"}

_api_key_header = APIKeyHeader(name=API_KEY_HEADER_NAME, auto_error=False)


def _key_is_valid(candidate: str, valid_keys: list[str]) -> bool:
    return any(hmac.compare_digest(candidate, key) for key in valid_keys)


async def require_api_key(
    request: Request,
    api_key: str | None = Security(_api_key_header),
) -> None:
    """FastAPI dependency enforcing the API-key gate when auth is enabled."""
    settings = get_settings()
    if not settings.auth_enabled:
        return None
    if request.url.path in _EXEMPT_PATHS:
        return None
    if api_key and _key_is_valid(api_key, settings.api_keys):
        return None
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Missing or invalid API key",
        headers={"WWW-Authenticate": API_KEY_HEADER_NAME},
    )
