from datetime import UTC, datetime
from inspect import iscoroutine
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import httpx2
import pytest
from redis import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.monitor import Monitor
from app.database.models.monitor_check import MonitorCheck
from app.modules.checks.engine import HttpCheckEngine
from app.modules.checks.service import CheckExecutionService
from app.modules.monitors.repository import MonitorRepository
from app.modules.realtime.events import RealtimePublisher
from app.workers.monitor_tasks import (
    check_monitor,
    execute_monitor_check,
    run_worker_coroutine,
)


def create_monitor(*, is_active: bool = True) -> Monitor:
    return Monitor(
        id=uuid4(),
        user_id=uuid4(),
        name="Production API",
        url="https://api.example.com/health",
        interval_seconds=60,
        timeout_seconds=5,
        expected_status=200,
        is_active=is_active,
        next_check_at=datetime(2026, 8, 8, tzinfo=UTC),
    )


@pytest.mark.anyio
@pytest.mark.anyio
async def test_execute_monitor_check_runs_active_monitor() -> None:
    session = AsyncMock(spec=AsyncSession)
    client = MagicMock(spec=httpx2.AsyncClient)
    repository = AsyncMock(spec=MonitorRepository)
    engine = MagicMock(spec=HttpCheckEngine)
    service = AsyncMock(spec=CheckExecutionService)
    realtime_publisher = AsyncMock(spec=RealtimePublisher)
    monitor = create_monitor()
    monitor_check = MonitorCheck(
        id=1,
        monitor_id=monitor.id,
        success=True,
        status_code=200,
        response_time_ms=125,
    )
    repository.get_by_id.return_value = monitor
    service.execute.return_value = monitor_check

    with (
        patch(
            "app.workers.monitor_tasks.MonitorRepository",
            return_value=repository,
        ),
        patch(
            "app.workers.monitor_tasks.HttpCheckEngine",
            return_value=engine,
        ),
        patch(
            "app.workers.monitor_tasks.CheckExecutionService",
            return_value=service,
        ) as service_class,
    ):
        result = await execute_monitor_check(
            monitor.id,
            session,
            client,
            realtime_publisher,
        )

    assert result is monitor_check
    session.commit.assert_awaited_once()
    repository.get_by_id.assert_awaited_once_with(monitor.id)
    service_class.assert_called_once_with(
        session=session,
        engine=engine,
        realtime_publisher=realtime_publisher,
    )
    service.execute.assert_awaited_once_with(monitor)


@pytest.mark.anyio
async def test_execute_monitor_check_skips_missing_monitor() -> None:
    session = AsyncMock(spec=AsyncSession)
    client = MagicMock(spec=httpx2.AsyncClient)
    repository = AsyncMock(spec=MonitorRepository)
    repository.get_by_id.return_value = None
    monitor_id = uuid4()

    with (
        patch(
            "app.workers.monitor_tasks.MonitorRepository",
            return_value=repository,
        ),
        patch(
            "app.workers.monitor_tasks.CheckExecutionService",
        ) as service_class,
    ):
        result = await execute_monitor_check(
            monitor_id,
            session,
            client,
        )

    assert result is None
    service_class.assert_not_called()


@pytest.mark.anyio
async def test_execute_monitor_check_skips_inactive_monitor() -> None:
    session = AsyncMock(spec=AsyncSession)
    client = MagicMock(spec=httpx2.AsyncClient)
    repository = AsyncMock(spec=MonitorRepository)
    monitor = create_monitor(is_active=False)
    repository.get_by_id.return_value = monitor

    with (
        patch(
            "app.workers.monitor_tasks.MonitorRepository",
            return_value=repository,
        ),
        patch(
            "app.workers.monitor_tasks.CheckExecutionService",
        ) as service_class,
    ):
        result = await execute_monitor_check(
            monitor.id,
            session,
            client,
        )

    assert result is None
    service_class.assert_not_called()


def test_check_monitor_skips_busy_lock() -> None:
    redis_client = MagicMock(spec=Redis)
    lock_context = MagicMock()
    lock_context.__enter__.return_value = False
    monitor_id = uuid4()

    with (
        patch(
            "app.workers.monitor_tasks.create_redis_client",
            return_value=redis_client,
        ),
        patch(
            "app.workers.monitor_tasks.acquire_monitor_lock",
            return_value=lock_context,
        ),
        patch("app.workers.monitor_tasks.asyncio.run") as runner,
    ):
        check_monitor.run(str(monitor_id))

    runner.assert_not_called()
    redis_client.close.assert_called_once()


def test_check_monitor_runs_with_acquired_lock() -> None:
    redis_client = MagicMock(spec=Redis)
    lock_context = MagicMock()
    lock_context.__enter__.return_value = True
    monitor_id = uuid4()

    with (
        patch(
            "app.workers.monitor_tasks.create_redis_client",
            return_value=redis_client,
        ),
        patch(
            "app.workers.monitor_tasks.acquire_monitor_lock",
            return_value=lock_context,
        ),
        patch("app.workers.monitor_tasks.asyncio.run") as runner,
    ):
        check_monitor.run(str(monitor_id))

    runner.assert_called_once()
    coroutine = runner.call_args.args[0]
    assert iscoroutine(coroutine)
    coroutine.close()
    redis_client.close.assert_called_once()


async def do_nothing() -> None:
    pass


def test_run_worker_coroutine_uses_selector_loop_on_windows() -> None:
    coroutine = do_nothing()

    with (
        patch("app.workers.monitor_tasks.sys.platform", "win32"),
        patch("app.workers.monitor_tasks.asyncio.run") as runner,
    ):
        run_worker_coroutine(coroutine)

    runner.assert_called_once()
    assert "loop_factory" in runner.call_args.kwargs
    coroutine.close()


def test_run_worker_coroutine_uses_default_loop_elsewhere() -> None:
    coroutine = do_nothing()

    with (
        patch("app.workers.monitor_tasks.sys.platform", "linux"),
        patch("app.workers.monitor_tasks.asyncio.run") as runner,
    ):
        run_worker_coroutine(coroutine)

    runner.assert_called_once_with(coroutine)
    coroutine.close()
