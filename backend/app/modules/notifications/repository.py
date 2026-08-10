from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.incident import Incident
from app.database.models.monitor import Monitor
from app.database.models.notification import Notification
from app.database.models.user import User
from app.modules.notifications.enums import (
    NotificationStatus,
)


@dataclass(frozen=True, slots=True)
class NotificationDeliveryContext:
    recipient_email: str
    monitor_name: str
    monitor_url: str
    failure_reason: str
    started_at: datetime
    resolved_at: datetime | None


class NotificationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add(
        self,
        notification: Notification,
    ) -> Notification:
        self.session.add(notification)
        await self.session.flush()

        return notification

    async def list_deliverable_ids(
        self,
        *,
        limit: int,
        max_attempts: int,
    ) -> list[UUID]:
        statement = (
            select(Notification.id)
            .where(
                Notification.status.in_(
                    (
                        NotificationStatus.PENDING,
                        NotificationStatus.FAILED,
                    )
                ),
                Notification.attempt_count < max_attempts,
            )
            .order_by(
                Notification.created_at.asc(),
                Notification.id.asc(),
            )
            .limit(limit)
        )
        result = await self.session.execute(statement)

        return list(result.scalars().all())

    async def get_for_update(
        self,
        notification_id: UUID,
    ) -> Notification | None:
        statement = (
            select(Notification)
            .where(Notification.id == notification_id)
            .with_for_update()
        )
        result = await self.session.execute(statement)

        return result.scalar_one_or_none()

    async def get_delivery_context(
        self,
        notification_id: UUID,
    ) -> NotificationDeliveryContext | None:
        statement = (
            select(
                User.email.label("recipient_email"),
                Monitor.name.label("monitor_name"),
                Monitor.url.label("monitor_url"),
                Incident.failure_reason.label("failure_reason"),
                Incident.started_at.label("started_at"),
                Incident.resolved_at.label("resolved_at"),
            )
            .select_from(Notification)
            .join(
                User,
                Notification.user_id == User.id,
            )
            .join(
                Incident,
                Notification.incident_id == Incident.id,
            )
            .join(
                Monitor,
                Incident.monitor_id == Monitor.id,
            )
            .where(Notification.id == notification_id)
        )
        result = await self.session.execute(statement)
        row = result.one_or_none()

        if row is None:
            return None

        return NotificationDeliveryContext(
            recipient_email=row.recipient_email,
            monitor_name=row.monitor_name,
            monitor_url=row.monitor_url,
            failure_reason=row.failure_reason,
            started_at=row.started_at,
            resolved_at=row.resolved_at,
        )
