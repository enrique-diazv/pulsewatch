from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
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
