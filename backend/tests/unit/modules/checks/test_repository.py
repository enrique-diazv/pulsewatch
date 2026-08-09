from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from sqlalchemy.dialects import postgresql
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.monitor_check import MonitorCheck
from app.modules.checks.repository import MonitorCheckRepository


@pytest.mark.anyio
async def test_add_flushes_monitor_check() -> None:
    session = AsyncMock(spec=AsyncSession)
    repository = MonitorCheckRepository(session)
    monitor_check = MonitorCheck(
        monitor_id=uuid4(),
        success=True,
        status_code=200,
        response_time_ms=125,
        error_type=None,
        error_message=None,
    )

    added_monitor_check = await repository.add(monitor_check)

    assert added_monitor_check is monitor_check
    session.add.assert_called_once_with(monitor_check)
    session.flush.assert_awaited_once()


@pytest.mark.anyio
async def test_list_for_monitor_returns_latest_checks_first() -> None:
    session = AsyncMock(spec=AsyncSession)
    result = MagicMock()
    monitor_id = uuid4()
    checks = [
        MonitorCheck(
            monitor_id=monitor_id,
            success=True,
            status_code=200,
            response_time_ms=125,
        ),
        MonitorCheck(
            monitor_id=monitor_id,
            success=False,
            status_code=503,
            response_time_ms=450,
        ),
    ]
    result.scalars.return_value.all.return_value = checks
    session.execute.return_value = result
    repository = MonitorCheckRepository(session)

    found_checks = await repository.list_for_monitor(
        monitor_id,
        limit=50,
    )

    assert found_checks == checks

    statement = session.execute.await_args.args[0]
    sql = str(
        statement.compile(
            dialect=postgresql.dialect(),
            compile_kwargs={"literal_binds": True},
        )
    )

    assert f"monitor_checks.monitor_id = '{monitor_id}'" in sql
    assert ("ORDER BY monitor_checks.checked_at DESC, monitor_checks.id DESC") in sql
    assert "LIMIT 50" in sql
