from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.dashboard.repository import DashboardRepository


@pytest.mark.anyio
async def test_summarize_for_user_returns_aggregated_data() -> None:
    session = AsyncMock(spec=AsyncSession)
    result = MagicMock()
    result.one.return_value = SimpleNamespace(
        total_monitors=12,
        operational_monitors=10,
        down_monitors=1,
        degraded_monitors=1,
        active_incidents=1,
        total_checks=1000,
        successful_checks=998,
        average_response_time_ms=184.5,
    )
    session.execute.return_value = result
    repository = DashboardRepository(session)

    summary = await repository.summarize_for_user(
        uuid4(),
    )

    assert summary.total_monitors == 12
    assert summary.operational_monitors == 10
    assert summary.active_incidents == 1
    assert summary.total_checks == 1000
    assert summary.successful_checks == 998
    assert summary.average_response_time_ms == 184.5
    session.execute.assert_awaited_once()


@pytest.mark.anyio
async def test_summarize_for_user_handles_empty_check_history() -> None:
    session = AsyncMock(spec=AsyncSession)
    result = MagicMock()
    result.one.return_value = SimpleNamespace(
        total_monitors=0,
        operational_monitors=0,
        down_monitors=0,
        degraded_monitors=0,
        active_incidents=0,
        total_checks=0,
        successful_checks=0,
        average_response_time_ms=None,
    )
    session.execute.return_value = result
    repository = DashboardRepository(session)

    summary = await repository.summarize_for_user(
        uuid4(),
    )

    assert summary.total_checks == 0
    assert summary.average_response_time_ms is None
