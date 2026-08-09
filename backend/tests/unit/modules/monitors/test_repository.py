from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from sqlalchemy.dialects import postgresql
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.monitor import Monitor
from app.modules.monitors.repository import MonitorRepository


def create_monitor() -> Monitor:
    return Monitor(
        user_id=uuid4(),
        name="Production API",
        url="https://api.example.com/health",
        interval_seconds=60,
        timeout_seconds=5,
        next_check_at=datetime.now(UTC),
    )


@pytest.mark.anyio
async def test_list_due_for_update_locks_batch_without_waiting() -> None:
    session = AsyncMock(spec=AsyncSession)
    result = MagicMock()
    monitors = [create_monitor(), create_monitor()]
    result.scalars.return_value.all.return_value = monitors
    session.execute.return_value = result
    repository = MonitorRepository(session)
    due_at = datetime(2026, 8, 9, tzinfo=UTC)

    due_monitors = await repository.list_due_for_update(
        due_at,
        limit=100,
    )

    assert due_monitors == monitors

    statement = session.execute.await_args.args[0]
    sql = str(
        statement.compile(
            dialect=postgresql.dialect(),
            compile_kwargs={"literal_binds": True},
        )
    )

    assert "monitors.next_check_at <=" in sql
    assert "ORDER BY monitors.next_check_at ASC, monitors.id ASC" in sql
    assert "LIMIT 100" in sql
    assert "FOR UPDATE SKIP LOCKED" in sql


@pytest.mark.anyio
async def test_add_flushes_monitor() -> None:
    session = AsyncMock(spec=AsyncSession)
    repository = MonitorRepository(session)
    monitor = create_monitor()

    added_monitor = await repository.add(monitor)

    assert added_monitor is monitor
    session.add.assert_called_once_with(monitor)
    session.flush.assert_awaited_once()


@pytest.mark.anyio
async def test_list_for_user_returns_user_monitors() -> None:
    session = AsyncMock(spec=AsyncSession)
    result = MagicMock()
    monitors = [create_monitor(), create_monitor()]
    result.scalars.return_value.all.return_value = monitors
    session.execute.return_value = result
    repository = MonitorRepository(session)
    user_id = uuid4()

    found_monitors = await repository.list_for_user(user_id)

    assert found_monitors == monitors
    session.execute.assert_awaited_once()


@pytest.mark.anyio
async def test_get_for_user_returns_owned_monitor() -> None:
    session = AsyncMock(spec=AsyncSession)
    result = MagicMock()
    monitor = create_monitor()
    result.scalar_one_or_none.return_value = monitor
    session.execute.return_value = result
    repository = MonitorRepository(session)

    found_monitor = await repository.get_for_user(
        monitor.id,
        monitor.user_id,
    )

    assert found_monitor is monitor
    session.execute.assert_awaited_once()


@pytest.mark.anyio
async def test_delete_removes_monitor() -> None:
    session = AsyncMock(spec=AsyncSession)
    repository = MonitorRepository(session)
    monitor = create_monitor()

    await repository.delete(monitor)

    session.delete.assert_awaited_once_with(monitor)


@pytest.mark.anyio
async def test_get_by_id_returns_monitor_for_worker() -> None:
    session = AsyncMock(spec=AsyncSession)
    result = MagicMock()
    monitor = create_monitor()
    result.scalar_one_or_none.return_value = monitor
    session.execute.return_value = result
    repository = MonitorRepository(session)

    found_monitor = await repository.get_by_id(monitor.id)

    assert found_monitor is monitor
    session.execute.assert_awaited_once()
