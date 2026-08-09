from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from sqlalchemy.dialects import postgresql
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.incident import Incident
from app.modules.incidents.enums import IncidentStatus
from app.modules.incidents.repository import IncidentRepository


def create_incident() -> Incident:
    return Incident(
        monitor_id=uuid4(),
        failure_reason="Request timeout",
        initial_check_id=42,
    )


@pytest.mark.anyio
async def test_add_flushes_incident() -> None:
    session = AsyncMock(spec=AsyncSession)
    repository = IncidentRepository(session)
    incident = create_incident()

    added_incident = await repository.add(incident)

    assert added_incident is incident
    session.add.assert_called_once_with(incident)
    session.flush.assert_awaited_once()


@pytest.mark.anyio
async def test_list_for_user_filters_by_owner_and_status() -> None:
    session = AsyncMock(spec=AsyncSession)
    result = MagicMock()
    incidents = [create_incident(), create_incident()]
    result.scalars.return_value.all.return_value = incidents
    session.execute.return_value = result
    repository = IncidentRepository(session)
    user_id = uuid4()

    found_incidents = await repository.list_for_user(
        user_id,
        status=IncidentStatus.OPEN,
    )

    assert found_incidents == incidents

    statement = session.execute.await_args.args[0]
    sql = str(
        statement.compile(
            dialect=postgresql.dialect(),
            compile_kwargs={"literal_binds": True},
        )
    )

    assert "JOIN monitors ON incidents.monitor_id = monitors.id" in sql
    assert "monitors.user_id =" in sql
    assert "incidents.status = 'OPEN'" in sql
    assert "ORDER BY incidents.started_at DESC, incidents.id DESC" in sql


@pytest.mark.anyio
async def test_get_for_user_enforces_monitor_ownership() -> None:
    session = AsyncMock(spec=AsyncSession)
    result = MagicMock()
    incident = create_incident()
    result.scalar_one_or_none.return_value = incident
    session.execute.return_value = result
    repository = IncidentRepository(session)

    found_incident = await repository.get_for_user(
        uuid4(),
        uuid4(),
    )

    assert found_incident is incident

    statement = session.execute.await_args.args[0]
    sql = str(
        statement.compile(
            dialect=postgresql.dialect(),
            compile_kwargs={"literal_binds": True},
        )
    )

    assert "JOIN monitors ON incidents.monitor_id = monitors.id" in sql
    assert "incidents.id =" in sql
    assert "monitors.user_id =" in sql


@pytest.mark.anyio
async def test_get_open_for_update_locks_open_incident() -> None:
    session = AsyncMock(spec=AsyncSession)
    result = MagicMock()
    incident = create_incident()
    result.scalar_one_or_none.return_value = incident
    session.execute.return_value = result
    repository = IncidentRepository(session)

    found_incident = await repository.get_open_for_update(
        incident.monitor_id,
    )

    assert found_incident is incident

    statement = session.execute.await_args.args[0]
    sql = str(
        statement.compile(
            dialect=postgresql.dialect(),
            compile_kwargs={"literal_binds": True},
        )
    )

    assert "incidents.monitor_id =" in sql
    assert "incidents.status = 'OPEN'" in sql
    assert "FOR UPDATE" in sql
