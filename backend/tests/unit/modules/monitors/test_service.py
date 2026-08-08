from datetime import UTC, datetime
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.monitor import Monitor
from app.modules.monitors.enums import MonitorStatus
from app.modules.monitors.exceptions import MonitorNotFoundError
from app.modules.monitors.repository import MonitorRepository
from app.modules.monitors.schemas import MonitorCreate, MonitorUpdate
from app.modules.monitors.service import MonitorService


@pytest.mark.anyio
async def test_create_builds_owned_monitor() -> None:
    session = AsyncMock(spec=AsyncSession)
    repository = AsyncMock(spec=MonitorRepository)
    repository.add.side_effect = lambda monitor: monitor
    service = MonitorService(
        session=session,
        repository=repository,
    )
    user_id = uuid4()
    created_at = datetime(2026, 8, 8, tzinfo=UTC)
    request = MonitorCreate(
        name="Production API",
        url="https://api.example.com/health",
    )

    monitor = await service.create(
        user_id,
        request,
        now=created_at,
    )

    assert monitor.user_id == user_id
    assert monitor.name == "Production API"
    assert monitor.url == "https://api.example.com/health"
    assert monitor.status is MonitorStatus.UNKNOWN
    assert monitor.is_active is True
    assert monitor.next_check_at == created_at
    repository.add.assert_awaited_once_with(monitor)
    session.commit.assert_awaited_once()
    session.refresh.assert_awaited_once_with(monitor)


@pytest.mark.anyio
async def test_list_for_user_returns_repository_results() -> None:
    session = AsyncMock(spec=AsyncSession)
    repository = AsyncMock(spec=MonitorRepository)
    repository.list_for_user.return_value = []
    service = MonitorService(
        session=session,
        repository=repository,
    )
    user_id = uuid4()

    monitors = await service.list_for_user(user_id)

    assert monitors == []
    repository.list_for_user.assert_awaited_once_with(user_id)


@pytest.mark.anyio
async def test_get_for_user_rejects_missing_or_unowned_monitor() -> None:
    session = AsyncMock(spec=AsyncSession)
    repository = AsyncMock(spec=MonitorRepository)
    repository.get_for_user.return_value = None
    service = MonitorService(
        session=session,
        repository=repository,
    )

    with pytest.raises(MonitorNotFoundError):
        await service.get_for_user(
            monitor_id=uuid4(),
            user_id=uuid4(),
        )


def create_owned_monitor() -> Monitor:
    return Monitor(
        id=uuid4(),
        user_id=uuid4(),
        name="Production API",
        url="https://api.example.com/health",
        interval_seconds=60,
        timeout_seconds=5,
        status=MonitorStatus.UNKNOWN,
        is_active=True,
        next_check_at=datetime(2026, 8, 8, tzinfo=UTC),
    )


@pytest.mark.anyio
async def test_update_changes_monitor_and_reschedules_check() -> None:
    session = AsyncMock(spec=AsyncSession)
    repository = AsyncMock(spec=MonitorRepository)
    monitor = create_owned_monitor()
    repository.get_for_user.return_value = monitor
    service = MonitorService(session=session, repository=repository)
    updated_at = datetime(2026, 8, 9, tzinfo=UTC)

    updated_monitor = await service.update(
        monitor.id,
        monitor.user_id,
        MonitorUpdate(
            name="Updated API",
            interval_seconds=120,
        ),
        now=updated_at,
    )

    assert updated_monitor is monitor
    assert monitor.name == "Updated API"
    assert monitor.interval_seconds == 120
    assert monitor.next_check_at == updated_at
    session.commit.assert_awaited_once()
    session.refresh.assert_awaited_once_with(monitor)


@pytest.mark.anyio
async def test_delete_removes_owned_monitor() -> None:
    session = AsyncMock(spec=AsyncSession)
    repository = AsyncMock(spec=MonitorRepository)
    monitor = create_owned_monitor()
    repository.get_for_user.return_value = monitor
    service = MonitorService(session=session, repository=repository)

    await service.delete(monitor.id, monitor.user_id)

    repository.delete.assert_awaited_once_with(monitor)
    session.commit.assert_awaited_once()


@pytest.mark.anyio
async def test_pause_marks_monitor_inactive() -> None:
    session = AsyncMock(spec=AsyncSession)
    repository = AsyncMock(spec=MonitorRepository)
    monitor = create_owned_monitor()
    repository.get_for_user.return_value = monitor
    service = MonitorService(session=session, repository=repository)

    paused_monitor = await service.pause(
        monitor.id,
        monitor.user_id,
    )

    assert paused_monitor.is_active is False
    assert paused_monitor.status is MonitorStatus.PAUSED
    session.commit.assert_awaited_once()


@pytest.mark.anyio
async def test_resume_marks_monitor_unknown_and_due() -> None:
    session = AsyncMock(spec=AsyncSession)
    repository = AsyncMock(spec=MonitorRepository)
    monitor = create_owned_monitor()
    monitor.is_active = False
    monitor.status = MonitorStatus.PAUSED
    repository.get_for_user.return_value = monitor
    service = MonitorService(session=session, repository=repository)
    resumed_at = datetime(2026, 8, 9, tzinfo=UTC)

    resumed_monitor = await service.resume(
        monitor.id,
        monitor.user_id,
        now=resumed_at,
    )

    assert resumed_monitor.is_active is True
    assert resumed_monitor.status is MonitorStatus.UNKNOWN
    assert resumed_monitor.next_check_at == resumed_at
    session.commit.assert_awaited_once()
