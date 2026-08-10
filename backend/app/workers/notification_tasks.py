from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.logging import get_logger
from app.database.session import async_session_factory
from app.integrations.email import (
    EmailSender,
    create_email_sender,
)
from app.integrations.redis import create_redis_client
from app.modules.notifications.enums import (
    NotificationStatus,
)
from app.modules.notifications.repository import (
    NotificationRepository,
)
from app.modules.notifications.service import (
    NotificationDeliveryService,
)
from app.workers.celery_app import celery_app
from app.workers.locks import acquire_notification_lock
from app.workers.monitor_tasks import run_worker_coroutine

logger = get_logger(__name__)


def enqueue_notification(
    notification_id: UUID,
) -> str:
    task = send_notification.apply_async(
        args=(str(notification_id),),
        queue="notifications",
    )

    return task.id


async def enqueue_pending_notifications(
    session: AsyncSession,
    *,
    batch_size: int,
    max_attempts: int,
) -> int:
    repository = NotificationRepository(session)
    notification_ids = await repository.list_deliverable_ids(
        limit=batch_size,
        max_attempts=max_attempts,
    )
    queued_count = 0

    for notification_id in notification_ids:
        try:
            enqueue_notification(notification_id)
        except Exception:
            logger.exception(
                "notification_enqueue_failed",
                extra={
                    "notification_id": str(notification_id),
                },
            )
        else:
            queued_count += 1

    return queued_count


async def deliver_notification(
    notification_id: UUID,
    session: AsyncSession,
    sender: EmailSender,
    *,
    max_attempts: int,
) -> NotificationStatus | None:
    service = NotificationDeliveryService(
        session,
        sender,
    )

    return await service.deliver(
        notification_id,
        max_attempts=max_attempts,
    )


async def _dispatch_pending_notifications_task() -> None:
    settings = get_settings()

    async with async_session_factory() as session:
        queued_count = await enqueue_pending_notifications(
            session,
            batch_size=settings.notification_batch_size,
            max_attempts=(settings.notification_max_attempts),
        )

    logger.info(
        "notification_dispatch_completed",
        extra={"queued_count": queued_count},
    )


async def _deliver_notification_task(
    notification_id: UUID,
) -> None:
    settings = get_settings()
    sender = create_email_sender(settings)

    async with async_session_factory() as session:
        result = await deliver_notification(
            notification_id,
            session,
            sender,
            max_attempts=(settings.notification_max_attempts),
        )

    logger.info(
        "notification_delivery_completed",
        extra={
            "notification_id": str(notification_id),
            "status": (result.value if result is not None else "MISSING"),
        },
    )


@celery_app.task(
    name=("app.workers.notification_tasks.dispatch_pending_notifications"),
)
def dispatch_pending_notifications() -> None:
    run_worker_coroutine(_dispatch_pending_notifications_task())


@celery_app.task(
    name="app.workers.notification_tasks.send_notification",
)
def send_notification(notification_id: str) -> None:
    parsed_notification_id = UUID(notification_id)
    redis_client = create_redis_client()

    try:
        with acquire_notification_lock(
            redis_client,
            parsed_notification_id,
        ) as acquired:
            if not acquired:
                logger.info(
                    "notification_delivery_skipped_locked",
                    extra={
                        "notification_id": notification_id,
                    },
                )
                return

            run_worker_coroutine(_deliver_notification_task(parsed_notification_id))
    finally:
        redis_client.close()
