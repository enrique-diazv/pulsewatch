from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.incident import Incident
from app.modules.incidents.enums import IncidentStatus
from app.modules.incidents.exceptions import IncidentNotFoundError
from app.modules.incidents.repository import IncidentRepository
from app.modules.incidents.service import IncidentService


def create_incident() -> Incident:
    return Incident(
        monitor_id=uuid4(),
        failure_reason="Request timed out",
        initial_check_id=42,
    )


@pytest.mark.anyio
async def test_list_for_user_returns_filtered_incidents() -> None:
    session = AsyncMock(spec=AsyncSession)
    repository = AsyncMock(spec=IncidentRepository)
    incidents = [create_incident()]
    repository.list_for_user.return_value = incidents
    service = IncidentService(
        session=session,
        repository=repository,
    )
    user_id = uuid4()

    found_incidents = await service.list_for_user(
        user_id,
        status=IncidentStatus.OPEN,
    )

    assert found_incidents == incidents
    repository.list_for_user.assert_awaited_once_with(
        user_id,
        status=IncidentStatus.OPEN,
    )


@pytest.mark.anyio
async def test_get_for_user_returns_owned_incident() -> None:
    session = AsyncMock(spec=AsyncSession)
    repository = AsyncMock(spec=IncidentRepository)
    incident = create_incident()
    repository.get_for_user.return_value = incident
    service = IncidentService(
        session=session,
        repository=repository,
    )

    found_incident = await service.get_for_user(
        uuid4(),
        uuid4(),
    )

    assert found_incident is incident


@pytest.mark.anyio
async def test_get_for_user_rejects_missing_or_unowned_incident() -> None:
    session = AsyncMock(spec=AsyncSession)
    repository = AsyncMock(spec=IncidentRepository)
    repository.get_for_user.return_value = None
    service = IncidentService(
        session=session,
        repository=repository,
    )

    with pytest.raises(
        IncidentNotFoundError,
        match="Incident not found",
    ):
        await service.get_for_user(
            uuid4(),
            uuid4(),
        )
