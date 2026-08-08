from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.monitor import Monitor
from app.database.models.user import User
from app.database.session import get_database_session
from app.modules.auth.dependencies import get_current_user
from app.modules.monitors.exceptions import MonitorNotFoundError
from app.modules.monitors.schemas import MonitorCreate, MonitorResponse, MonitorUpdate
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
