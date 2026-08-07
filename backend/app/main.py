from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.health import router as health_router
from app.api.v1.router import router as api_v1_router
from app.core.config import get_settings
from app.core.logging import configure_logging, get_logger
from app.database.session import database_engine

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    configure_logging(settings.log_level)

    logger.info(
        "application_started",
        extra={
            "environment": settings.environment,
            "version": settings.app_version,
        },
    )

    try:
        yield
    finally:
        await database_engine.dispose()
        logger.info("application_stopped")


def create_app() -> FastAPI:
    settings = get_settings()

    application = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        debug=settings.debug,
        lifespan=lifespan,
    )
    application.include_router(health_router)
    application.include_router(api_v1_router)
    return application


app = create_app()
