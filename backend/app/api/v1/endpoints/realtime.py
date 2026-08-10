from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import APIRouter, Depends, Query, WebSocket, status
from redis.asyncio import Redis as AsyncRedis

from app.core.config import get_settings
from app.database.models.user import User
from app.integrations.redis import create_async_redis_client
from app.modules.auth.dependencies import get_current_user
from app.modules.realtime.connections import stream_user_events
from app.modules.realtime.events import build_user_channel
from app.modules.realtime.schemas import RealtimeTicketResponse
from app.modules.realtime.tickets import RealtimeTicketService

router = APIRouter(
    prefix="/realtime",
    tags=["realtime"],
)

CurrentUser = Annotated[
    User,
    Depends(get_current_user),
]


async def get_realtime_redis() -> AsyncIterator[AsyncRedis]:
    redis_client = create_async_redis_client()

    try:
        yield redis_client
    finally:
        await redis_client.aclose()


RealtimeRedis = Annotated[
    AsyncRedis,
    Depends(get_realtime_redis),
]


@router.post(
    "/ticket",
    response_model=RealtimeTicketResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Issue realtime connection ticket",
)
async def issue_realtime_ticket(
    current_user: CurrentUser,
    redis_client: RealtimeRedis,
) -> RealtimeTicketResponse:
    settings = get_settings()
    ticket = await RealtimeTicketService(
        redis_client,
        ttl_seconds=settings.realtime_ticket_ttl_seconds,
    ).issue(current_user.id)

    return RealtimeTicketResponse(
        ticket=ticket,
        expires_in=settings.realtime_ticket_ttl_seconds,
    )


@router.websocket("/ws")
async def connect_realtime(
    websocket: WebSocket,
    redis_client: RealtimeRedis,
    ticket: Annotated[str, Query(min_length=32)],
) -> None:
    settings = get_settings()
    user_id = await RealtimeTicketService(
        redis_client,
        ttl_seconds=settings.realtime_ticket_ttl_seconds,
    ).consume(ticket)

    if user_id is None:
        await websocket.close(
            code=status.WS_1008_POLICY_VIOLATION,
            reason="Invalid or expired realtime ticket",
        )
        return

    subscription = redis_client.pubsub()

    await stream_user_events(
        websocket,
        subscription,
        build_user_channel(user_id),
    )
