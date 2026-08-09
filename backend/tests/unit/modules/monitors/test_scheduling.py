from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.monitor import Monitor
from app.modules.monitors.repository import MonitorRepository
from app.modules.monitors.scheduling import MonitorSchedulingService


def create_monitor(interval_seconds: int) -> Monitor:
    return Monitor(
        id=uuid4(),
        user_id=uuid4(),
        name="Scheduled API",
        url="https://api.example.com/health",
        interval_seconds=interval_seconds,
        timeout_seconds=5,
        expected_status=200,
        is_active=True,
        next_check_at=datetime(2026, 8, 8, tzinfo=UTC),
    )


@pytest.mark.anyio
async def test_claim_due_monitors_reschedules_batch() -> None:
    session = AsyncMock(spec=AsyncSession)
    repository = AsyncMock(spec=MonitorRepository)
    first_monitor = create_monitor(60)
    second_monitor = create_monitor(120)
    repository.list_due_for_update.return_value = [
        first_monitor,
        second_monitor,
    ]
    service = MonitorSchedulingService(
        session=session,
        repository=repository,
    )
    claimed_at = datetime(2026, 8, 9, tzinfo=UTC)

    monitor_ids = await service.claim_due_monitors(
        limit=100,
        now=claimed_at,
    )

    assert monitor_ids == [
        first_monitor.id,
        second_monitor.id,
    ]
    assert first_monitor.next_check_at == claimed_at + timedelta(
        seconds=60,
    )
    assert second_monitor.next_check_at == claimed_at + timedelta(
        seconds=120,
    )
    repository.list_due_for_update.assert_awaited_once_with(
        claimed_at,
        limit=100,
    )
    session.commit.assert_awaited_once()


@pytest.mark.anyio
async def test_claim_due_monitors_commits_empty_claim() -> None:
    session = AsyncMock(spec=AsyncSession)
    repository = AsyncMock(spec=MonitorRepository)
    repository.list_due_for_update.return_value = []
    service = MonitorSchedulingService(
        session=session,
        repository=repository,
    )

    monitor_ids = await service.claim_due_monitors(limit=100)

    assert monitor_ids == []
    session.commit.assert_awaited_once()
