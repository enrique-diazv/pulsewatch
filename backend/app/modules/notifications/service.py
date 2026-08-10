from collections.abc import Callable
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.integrations.email import EmailSender
from app.modules.notifications.email import (
    build_incident_email,
)
from app.modules.notifications.enums import (
    NotificationStatus,
)
from app.modules.notifications.repository import (
    NotificationRepository,
)


def utc_now() -> datetime:
    return datetime.now(UTC)


class NotificationDeliveryService:
    def __init__(
        self,
        session: AsyncSession,
        sender: EmailSender,
        repository: NotificationRepository | None = None,
        clock: Callable[[], datetime] = utc_now,
    ) -> None:
        self.session = session
        self.sender = sender
        self.repository = repository or NotificationRepository(session)
        self.clock = clock

    async def deliver(
        self,
        notification_id: UUID,
        *,
        max_attempts: int,
    ) -> NotificationStatus | None:
        notification = await self.repository.get_for_update(notification_id)

        if notification is None:
            await self.session.commit()
            return None

        if notification.status is NotificationStatus.SENT:
            await self.session.commit()
            return NotificationStatus.SENT

        if notification.attempt_count >= max_attempts:
            await self.session.commit()
            return notification.status

        context = await self.repository.get_delivery_context(notification_id)
        notification.attempt_count += 1

        if context is None:
            notification.status = NotificationStatus.FAILED
            notification.last_error = "Notification delivery context not found"
            await self.session.commit()

            return NotificationStatus.FAILED

        try:
            message = build_incident_email(
                notification_type=notification.type,
                recipient=context.recipient_email,
                monitor_name=context.monitor_name,
                monitor_url=context.monitor_url,
                failure_reason=context.failure_reason,
                started_at=context.started_at,
                resolved_at=context.resolved_at,
            )
            await self.sender.send(message)
        except Exception as error:
            notification.status = NotificationStatus.FAILED
            notification.last_error = (f"{type(error).__name__}: {error}")[:500]
            await self.session.commit()

            return NotificationStatus.FAILED

        notification.status = NotificationStatus.SENT
        notification.sent_at = self.clock()
        notification.last_error = None
        await self.session.commit()

        return NotificationStatus.SENT
