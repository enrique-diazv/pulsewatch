from inspect import iscoroutine
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from redis import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.integrations.email import EmailSender
from app.modules.notifications.enums import (
    NotificationStatus,
)
from app.modules.notifications.repository import (
    NotificationRepository,
)
from app.modules.notifications.service import (
    NotificationDeliveryService,
)
from app.workers.notification_tasks import (
    deliver_notification,
    dispatch_pending_notifications,
    enqueue_notification,
    enqueue_pending_notifications,
    send_notification,
)


def test_enqueue_notification_uses_notification_queue() -> None:
    notification_id = uuid4()
    task_result = MagicMock()
    task_result.id = "task-id"

    with patch(
        "app.workers.notification_tasks.send_notification.apply_async",
        return_value=task_result,
    ) as apply_async:
        task_id = enqueue_notification(notification_id)

    assert task_id == "task-id"
    apply_async.assert_called_once_with(
        args=(str(notification_id),),
        queue="notifications",
    )


@pytest.mark.anyio
async def test_enqueue_pending_notifications_queues_batch() -> None:
    session = AsyncMock(spec=AsyncSession)
    repository = AsyncMock(spec=NotificationRepository)
    notification_ids = [uuid4(), uuid4()]
    repository.list_deliverable_ids.return_value = notification_ids

    with (
        patch(
            "app.workers.notification_tasks.NotificationRepository",
            return_value=repository,
        ),
        patch(
            "app.workers.notification_tasks.enqueue_notification",
        ) as enqueue,
    ):
        queued_count = await enqueue_pending_notifications(
            session,
            batch_size=100,
            max_attempts=3,
        )

    assert queued_count == 2
    repository.list_deliverable_ids.assert_awaited_once_with(
        limit=100,
        max_attempts=3,
    )
    enqueue.assert_any_call(notification_ids[0])
    enqueue.assert_any_call(notification_ids[1])


@pytest.mark.anyio
async def test_enqueue_pending_continues_after_error() -> None:
    session = AsyncMock(spec=AsyncSession)
    repository = AsyncMock(spec=NotificationRepository)
    notification_ids = [uuid4(), uuid4()]
    repository.list_deliverable_ids.return_value = notification_ids

    with (
        patch(
            "app.workers.notification_tasks.NotificationRepository",
            return_value=repository,
        ),
        patch(
            "app.workers.notification_tasks.enqueue_notification",
            side_effect=[
                RuntimeError("Broker unavailable"),
                "task-id",
            ],
        ),
        patch(
            "app.workers.notification_tasks.logger.exception",
        ) as log_exception,
    ):
        queued_count = await enqueue_pending_notifications(
            session,
            batch_size=100,
            max_attempts=3,
        )

    assert queued_count == 1
    log_exception.assert_called_once()


@pytest.mark.anyio
async def test_deliver_notification_uses_service() -> None:
    session = AsyncMock(spec=AsyncSession)
    sender = MagicMock(spec=EmailSender)
    service = AsyncMock(spec=NotificationDeliveryService)
    service.deliver.return_value = NotificationStatus.SENT
    notification_id = uuid4()

    with patch(
        "app.workers.notification_tasks.NotificationDeliveryService",
        return_value=service,
    ) as service_class:
        result = await deliver_notification(
            notification_id,
            session,
            sender,
            max_attempts=3,
        )

    assert result is NotificationStatus.SENT
    service_class.assert_called_once_with(
        session,
        sender,
    )
    service.deliver.assert_awaited_once_with(
        notification_id,
        max_attempts=3,
    )


def test_dispatch_task_runs_async_dispatcher() -> None:
    with patch(
        "app.workers.notification_tasks.run_worker_coroutine",
    ) as runner:
        dispatch_pending_notifications.run()

    runner.assert_called_once()
    coroutine = runner.call_args.args[0]
    assert iscoroutine(coroutine)
    coroutine.close()


def test_send_notification_skips_busy_lock() -> None:
    redis_client = MagicMock(spec=Redis)
    lock_context = MagicMock()
    lock_context.__enter__.return_value = False
    notification_id = uuid4()

    with (
        patch(
            "app.workers.notification_tasks.create_redis_client",
            return_value=redis_client,
        ),
        patch(
            "app.workers.notification_tasks.acquire_notification_lock",
            return_value=lock_context,
        ),
        patch(
            "app.workers.notification_tasks.run_worker_coroutine",
        ) as runner,
    ):
        send_notification.run(str(notification_id))

    runner.assert_not_called()
    redis_client.close.assert_called_once()


def test_send_notification_runs_with_lock() -> None:
    redis_client = MagicMock(spec=Redis)
    lock_context = MagicMock()
    lock_context.__enter__.return_value = True
    notification_id = uuid4()

    with (
        patch(
            "app.workers.notification_tasks.create_redis_client",
            return_value=redis_client,
        ),
        patch(
            "app.workers.notification_tasks.acquire_notification_lock",
            return_value=lock_context,
        ),
        patch(
            "app.workers.notification_tasks.run_worker_coroutine",
        ) as runner,
    ):
        send_notification.run(str(notification_id))

    runner.assert_called_once()
    coroutine = runner.call_args.args[0]
    assert iscoroutine(coroutine)
    coroutine.close()
    redis_client.close.assert_called_once()
