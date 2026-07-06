"""AgentShadow FastAPI application entrypoint."""

from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import __version__
from app.api.routes import router
from app.core.auth import require_api_key
from app.core.config import get_settings
from app.core.logging import get_logger
from app.services import inventory_store

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    inventory_store.init_db()
    logger.info(
        "AgentShadow %s started (inventory at %s, auth %s)",
        __version__,
        settings.inventory_db_path,
        "enabled" if settings.auth_enabled else "disabled",
    )
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="AgentShadow API",
        version=__version__,
        description=(
            "Discover, inventory, risk-score, report on, and govern AI agents. "
            "Reuses the Valo deterministic scoring + policy engine, LLMShadow-style "
            "framework detection, and SaaSShadow inventory patterns."
        ),
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(router, dependencies=[Depends(require_api_key)])
    return app


app = create_app()
