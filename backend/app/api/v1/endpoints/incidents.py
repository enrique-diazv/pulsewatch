from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.incident import Incident
from app.database.models.user import User
from app.database.session import get_database_session
from app.modules.auth.dependencies import get_current_user
from app.modules.incidents.enums import IncidentStatus
from app.modules.incidents.exceptions import IncidentNotFoundError
from app.modules.incidents.schemas import IncidentResponse
from app.modules.incidents.service import IncidentService

router = APIRouter(prefix="/incidents", tags=["incidents"])

DatabaseSession = Annotated[
    AsyncSession,
    Depends(get_database_session),
]
CurrentUser = Annotated[
    User,
    Depends(get_current_user),
]
IncidentStatusFilter = Annotated[
    IncidentStatus | None,
    Query(alias="status"),
]


@router.get(
    "",
    response_model=list[IncidentResponse],
    summary="List incidents",
)
async def list_incidents(
    current_user: CurrentUser,
    session: DatabaseSession,
    status_filter: IncidentStatusFilter = None,
) -> list[Incident]:
    return await IncidentService(session).list_for_user(
        current_user.id,
        status=status_filter,
    )


@router.get(
    "/{incident_id}",
    response_model=IncidentResponse,
    summary="Get incident",
)
async def get_incident(
    incident_id: UUID,
    current_user: CurrentUser,
    session: DatabaseSession,
) -> Incident:
    try:
        return await IncidentService(session).get_for_user(
            incident_id,
            current_user.id,
        )
    except IncidentNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error
