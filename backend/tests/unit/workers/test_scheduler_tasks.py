from inspect import iscoroutine
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.monitors.scheduling import MonitorSchedulingService
from app.workers.scheduler_tasks import (
    enqueue_due_monitors,
    schedule_due_monitors,
)


@pytest.mark.anyio
async def test_enqueue_due_monitors_queues_claimed_batch() -> None:
    session = AsyncMock(spec=AsyncSession)
    service = AsyncMock(spec=MonitorSchedulingService)
    monitor_ids = [uuid4(), uuid4()]
    service.claim_due_monitors.return_value = monitor_ids

    with (
        patch(
            "app.workers.scheduler_tasks.MonitorSchedulingService",
            return_value=service,
        ),
        patch(
            "app.workers.scheduler_tasks.enqueue_monitor_check",
        ) as enqueue,
    ):
        queued_count = await enqueue_due_monitors(
            session,
            batch_size=100,
        )

    assert queued_count == 2
    service.claim_due_monitors.assert_awaited_once_with(
        limit=100,
    )
    assert enqueue.call_count == 2
    enqueue.assert_any_call(monitor_ids[0])
    enqueue.assert_any_call(monitor_ids[1])


@pytest.mark.anyio
async def test_enqueue_due_monitors_continues_after_enqueue_error() -> None:
    session = AsyncMock(spec=AsyncSession)
    service = AsyncMock(spec=MonitorSchedulingService)
    monitor_ids = [uuid4(), uuid4()]
    service.claim_due_monitors.return_value = monitor_ids

    with (
        patch(
            "app.workers.scheduler_tasks.MonitorSchedulingService",
            return_value=service,
        ),
        patch(
            "app.workers.scheduler_tasks.enqueue_monitor_check",
            side_effect=[RuntimeError("broker unavailable"), "task-id"],
        ) as enqueue,
        patch(
            "app.workers.scheduler_tasks.logger.exception",
        ) as log_exception,
    ):
        queued_count = await enqueue_due_monitors(
            session,
            batch_size=100,
        )

    assert queued_count == 1
    assert enqueue.call_count == 2
    log_exception.assert_called_once()


def test_schedule_due_monitors_runs_async_task() -> None:
    with patch(
        "app.workers.scheduler_tasks.run_worker_coroutine",
    ) as runner:
        schedule_due_monitors.run()

    runner.assert_called_once()
    coroutine = runner.call_args.args[0]
    assert iscoroutine(coroutine)
    coroutine.close()
