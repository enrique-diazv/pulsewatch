from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import APIRouter, Depends
from redis.asyncio import Redis as AsyncRedis
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.user import User
from app.database.session import get_database_session
from app.integrations.redis import create_async_redis_client
from app.modules.auth.dependencies import get_current_user
from app.modules.dashboard.schemas import DashboardSummary
from app.modules.dashboard.service import DashboardService

router = APIRouter(
    prefix="/dashboard",
    tags=["dashboard"],
)

DatabaseSession = Annotated[
    AsyncSession,
    Depends(get_database_session),
]
CurrentUser = Annotated[
    User,
    Depends(get_current_user),
]


async def get_dashboard_redis() -> AsyncIterator[AsyncRedis]:
    redis_client = create_async_redis_client()

    try:
        yield redis_client
    finally:
        await redis_client.aclose()


DashboardRedis = Annotated[
    AsyncRedis,
    Depends(get_dashboard_redis),
]


@router.get(
    "/summary",
    response_model=DashboardSummary,
    summary="Get dashboard summary",
)
async def get_dashboard_summary(
    current_user: CurrentUser,
    session: DatabaseSession,
    redis_client: DashboardRedis,
) -> DashboardSummary:
    return await DashboardService(
        session,
        redis_client,
    ).get_summary(current_user.id)
