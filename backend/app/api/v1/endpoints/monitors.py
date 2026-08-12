from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.database.models.monitor import Monitor
from app.database.models.user import User
from app.database.session import get_database_session
from app.modules.auth.dependencies import get_current_user
from app.modules.checks.cursors import (
    InvalidCheckCursorError,
    decode_check_cursor,
)
from app.modules.checks.queue import enqueue_monitor_check
from app.modules.checks.rate_limit import reserve_manual_check_slot
from app.modules.checks.repository import MonitorCheckRepository
from app.modules.checks.schemas import (
    CheckQueuedResponse,
    MetricsRange,
    MonitorCheckPageResponse,
    MonitorMetricsResponse,
)
from app.modules.checks.service import MonitorMetricsService
from app.modules.monitors.exceptions import MonitorNotFoundError
from app.modules.monitors.schemas import (
    MonitorCreate,
    MonitorResponse,
    MonitorUpdate,
)
from app.modules.monitors.service import MonitorService

router = APIRouter(prefix="/monitors", tags=["monitors"])

DatabaseSession = Annotated[
    AsyncSession,
    Depends(get_database_session),
]
CurrentUser = Annotated[
    User,
    Depends(get_current_user),
]


@router.post(
    "",
    response_model=MonitorResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create monitor",
)
async def create_monitor(
    request: MonitorCreate,
    current_user: CurrentUser,
    session: DatabaseSession,
) -> Monitor:
    return await MonitorService(session).create(
        current_user.id,
        request,
    )


@router.get(
    "",
    response_model=list[MonitorResponse],
    summary="List monitors",
)
async def list_monitors(
    current_user: CurrentUser,
    session: DatabaseSession,
) -> list[Monitor]:
    return await MonitorService(session).list_for_user(
        current_user.id,
    )


@router.get(
    "/{monitor_id}/checks",
    response_model=MonitorCheckPageResponse,
    summary="List monitor checks",
)
async def list_monitor_checks(
    monitor_id: UUID,
    current_user: CurrentUser,
    session: DatabaseSession,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
    cursor: Annotated[
        str | None,
        Query(min_length=1),
    ] = None,
) -> MonitorCheckPageResponse:
    try:
        await MonitorService(session).get_for_user(
            monitor_id,
            current_user.id,
        )
    except MonitorNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error

    try:
        decoded_cursor = decode_check_cursor(cursor) if cursor is not None else None
    except InvalidCheckCursorError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(error),
        ) from error

    page = await MonitorCheckRepository(session).list_page_for_monitor(
        monitor_id,
        limit=limit,
        cursor=decoded_cursor,
    )

    return MonitorCheckPageResponse(
        items=page.items,
        next_cursor=page.next_cursor,
    )


@router.get(
    "/{monitor_id}/metrics",
    response_model=MonitorMetricsResponse,
    summary="Get monitor metrics",
)
async def get_monitor_metrics(
    monitor_id: UUID,
    current_user: CurrentUser,
    session: DatabaseSession,
    metrics_range: Annotated[
        MetricsRange,
        Query(alias="range"),
    ] = "24h",
) -> MonitorMetricsResponse:
    try:
        await MonitorService(session).get_for_user(
            monitor_id,
            current_user.id,
        )
    except MonitorNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error

    return await MonitorMetricsService(session).summarize(
        monitor_id,
        metrics_range,
    )


@router.get(
    "/{monitor_id}",
    response_model=MonitorResponse,
    summary="Get monitor",
)
async def get_monitor(
    monitor_id: UUID,
    current_user: CurrentUser,
    session: DatabaseSession,
) -> Monitor:
    try:
        return await MonitorService(session).get_for_user(
            monitor_id,
            current_user.id,
        )
    except MonitorNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error


@router.patch(
    "/{monitor_id}",
    response_model=MonitorResponse,
    summary="Update monitor",
)
async def update_monitor(
    monitor_id: UUID,
    request: MonitorUpdate,
    current_user: CurrentUser,
    session: DatabaseSession,
) -> Monitor:
    try:
        return await MonitorService(session).update(
            monitor_id,
            current_user.id,
            request,
        )
    except MonitorNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error


@router.delete(
    "/{monitor_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete monitor",
)
async def delete_monitor(
    monitor_id: UUID,
    current_user: CurrentUser,
    session: DatabaseSession,
) -> None:
    try:
        await MonitorService(session).delete(
            monitor_id,
            current_user.id,
        )
    except MonitorNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error


@router.post(
    "/{monitor_id}/pause",
    response_model=MonitorResponse,
    summary="Pause monitor",
)
async def pause_monitor(
    monitor_id: UUID,
    current_user: CurrentUser,
    session: DatabaseSession,
) -> Monitor:
    try:
        return await MonitorService(session).pause(
            monitor_id,
            current_user.id,
        )
    except MonitorNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error


@router.post(
    "/{monitor_id}/resume",
    response_model=MonitorResponse,
    summary="Resume monitor",
)
async def resume_monitor(
    monitor_id: UUID,
    current_user: CurrentUser,
    session: DatabaseSession,
) -> Monitor:
    try:
        return await MonitorService(session).resume(
            monitor_id,
            current_user.id,
        )
    except MonitorNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error


@router.post(
    "/{monitor_id}/check",
    response_model=CheckQueuedResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Queue manual monitor check",
)
async def queue_manual_monitor_check(
    monitor_id: UUID,
    current_user: CurrentUser,
    session: DatabaseSession,
) -> CheckQueuedResponse:
    try:
        monitor = await MonitorService(session).get_for_user(
            monitor_id,
            current_user.id,
        )
    except MonitorNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error
    reserved = await reserve_manual_check_slot(
        current_user.id,
        monitor.id,
    )

    if not reserved:
        cooldown_seconds = get_settings().manual_check_cooldown_seconds

        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Manual check cooldown active",
            headers={"Retry-After": str(cooldown_seconds)},
        )
    task_id = enqueue_monitor_check(monitor.id)

    return CheckQueuedResponse(task_id=task_id)
