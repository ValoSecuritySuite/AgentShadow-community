"""Edition gating for AgentShadow.

This build ships as the free **Community Edition**. A handful of premium
capabilities (live runtime/SaaS connectors, PDF assessment exports, and the
shared correlation-engine feed) are present in the codebase but gated behind an
upgrade so the running app doubles as an advert for AgentShadow Pro/Enterprise.

Set ``APP_EDITION=pro`` (or ``enterprise``) to unlock everything at runtime,
which is also how the automated tests exercise the premium endpoints.
"""

import os
from functools import lru_cache

from fastapi import HTTPException

COMMUNITY = "community"


@lru_cache(maxsize=1)
def get_edition() -> str:
    return os.getenv("APP_EDITION", COMMUNITY).strip().lower() or COMMUNITY


def get_upgrade_url() -> str:
    return os.getenv("APP_UPGRADE_URL", "http://localhost:3011/pricing")


def is_community() -> bool:
    return get_edition() == COMMUNITY


# Premium features that are visible-but-locked in the Community Edition. The
# frontend reads this same catalogue (via ``GET /meta``) to render "PRO" badges
# and upgrade CTAs, so the two stay in lock-step.
LOCKED_FEATURES: dict[str, dict[str, str]] = {
    "runtime_connectors": {
        "title": "Runtime & SaaS connectors",
        "description": (
            "Discover live, deployed agents through provider APIs "
            "(OpenAI Assistants and more)."
        ),
        "tier": "Pro",
    },
    "pdf_reports": {
        "title": "PDF assessment reports",
        "description": "Branded, one-click PDF risk assessments for auditors and reviews.",
        "tier": "Pro",
    },
    "correlation": {
        "title": "Correlation engine feed",
        "description": "Feed discovered agents into the shared Valo cross-tool asset graph.",
        "tier": "Enterprise",
    },
}

# Capabilities that are fully functional in the Community Edition.
COMMUNITY_FEATURES: list[str] = [
    "Source-code agent discovery (LangChain, CrewAI, AutoGPT, AutoGen, ...)",
    "Deterministic 0-100 risk scoring",
    "Agent inventory with filters",
    "Executive dashboard",
    "Governance policy viewing",
]


def require_pro(feature_key: str) -> None:
    """Raise HTTP 402 with an upsell payload when a locked feature is used.

    No-op when running as Pro/Enterprise (``APP_EDITION`` overridden).
    """
    if not is_community():
        return
    feature = LOCKED_FEATURES.get(feature_key, {})
    tier = feature.get("tier", "Pro")
    title = feature.get("title", "This feature")
    raise HTTPException(
        status_code=402,
        detail={
            "error": "upgrade_required",
            "feature": feature_key,
            "title": title,
            "tier": tier,
            "message": f"{title} is available in AgentShadow {tier}. Upgrade to unlock it.",
            "upgrade_url": get_upgrade_url(),
        },
    )


def edition_meta() -> dict:
    """Payload for the ``GET /meta`` endpoint consumed by the frontend."""
    return {
        "edition": get_edition(),
        "is_community": is_community(),
        "upgrade_url": get_upgrade_url(),
        "community_features": COMMUNITY_FEATURES,
        "locked_features": LOCKED_FEATURES,
    }
