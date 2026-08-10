from datetime import UTC, datetime
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.notification import Notification
from app.integrations.email import EmailSender
from app.modules.notifications.enums import (
    NotificationStatus,
    NotificationType,
)
from app.modules.notifications.repository import (
    NotificationDeliveryContext,
    NotificationRepository,
)
from app.modules.notifications.service import (
    NotificationDeliveryService,
)

NOW = datetime(2026, 8, 9, 20, 0, tzinfo=UTC)
STARTED_AT = datetime(2026, 8, 9, 19, 52, tzinfo=UTC)


def create_notification(
    *,
    status: NotificationStatus = NotificationStatus.PENDING,
    attempt_count: int = 0,
) -> Notification:
    return Notification(
        id=uuid4(),
        user_id=uuid4(),
        incident_id=uuid4(),
        type=NotificationType.INCIDENT_OPENED,
        status=status,
        attempt_count=attempt_count,
    )


def create_context() -> NotificationDeliveryContext:
    return NotificationDeliveryContext(
        recipient_email="owner@example.com",
        monitor_name="Production API",
        monitor_url="https://api.example.com/health",
        failure_reason="Request timed out",
        started_at=STARTED_AT,
        resolved_at=None,
    )


@pytest.mark.anyio
async def test_deliver_sends_and_marks_notification_sent() -> None:
    session = AsyncMock(spec=AsyncSession)
    sender = AsyncMock(spec=EmailSender)
    repository = AsyncMock(spec=NotificationRepository)
    notification = create_notification()
    repository.get_for_update.return_value = notification
    repository.get_delivery_context.return_value = create_context()
    service = NotificationDeliveryService(
        session,
        sender,
        repository=repository,
        clock=lambda: NOW,
    )

    result = await service.deliver(
        notification.id,
        max_attempts=3,
    )

    assert result is NotificationStatus.SENT
    assert notification.status is NotificationStatus.SENT
    assert notification.attempt_count == 1
    assert notification.sent_at == NOW
    assert notification.last_error is None
    sender.send.assert_awaited_once()
    message = sender.send.await_args.args[0]
    assert message.recipient == "owner@example.com"
    assert message.subject == ("PulseWatch alert: Production API is down")
    session.commit.assert_awaited_once()


@pytest.mark.anyio
async def test_deliver_records_sender_failure() -> None:
    session = AsyncMock(spec=AsyncSession)
    sender = AsyncMock(spec=EmailSender)
    sender.send.side_effect = RuntimeError("SMTP unavailable")
    repository = AsyncMock(spec=NotificationRepository)
    notification = create_notification()
    repository.get_for_update.return_value = notification
    repository.get_delivery_context.return_value = create_context()
    service = NotificationDeliveryService(
        session,
        sender,
        repository=repository,
    )

    result = await service.deliver(
        notification.id,
        max_attempts=3,
    )

    assert result is NotificationStatus.FAILED
    assert notification.status is NotificationStatus.FAILED
    assert notification.attempt_count == 1
    assert notification.sent_at is None
    assert notification.last_error == ("RuntimeError: SMTP unavailable")
    session.commit.assert_awaited_once()


@pytest.mark.anyio
async def test_deliver_fails_when_context_is_missing() -> None:
    session = AsyncMock(spec=AsyncSession)
    sender = AsyncMock(spec=EmailSender)
    repository = AsyncMock(spec=NotificationRepository)
    notification = create_notification()
    repository.get_for_update.return_value = notification
    repository.get_delivery_context.return_value = None
    service = NotificationDeliveryService(
        session,
        sender,
        repository=repository,
    )

    result = await service.deliver(
        notification.id,
        max_attempts=3,
    )

    assert result is NotificationStatus.FAILED
    assert notification.attempt_count == 1
    assert notification.last_error == ("Notification delivery context not found")
    sender.send.assert_not_awaited()
    session.commit.assert_awaited_once()


@pytest.mark.anyio
async def test_deliver_skips_already_sent_notification() -> None:
    session = AsyncMock(spec=AsyncSession)
    sender = AsyncMock(spec=EmailSender)
    repository = AsyncMock(spec=NotificationRepository)
    notification = create_notification(
        status=NotificationStatus.SENT,
        attempt_count=1,
    )
    notification.sent_at = NOW
    repository.get_for_update.return_value = notification
    service = NotificationDeliveryService(
        session,
        sender,
        repository=repository,
    )

    result = await service.deliver(
        notification.id,
        max_attempts=3,
    )

    assert result is NotificationStatus.SENT
    repository.get_delivery_context.assert_not_awaited()
    sender.send.assert_not_awaited()
    session.commit.assert_awaited_once()


@pytest.mark.anyio
async def test_deliver_stops_after_maximum_attempts() -> None:
    session = AsyncMock(spec=AsyncSession)
    sender = AsyncMock(spec=EmailSender)
    repository = AsyncMock(spec=NotificationRepository)
    notification = create_notification(
        status=NotificationStatus.FAILED,
        attempt_count=3,
    )
    repository.get_for_update.return_value = notification
    service = NotificationDeliveryService(
        session,
        sender,
        repository=repository,
    )

    result = await service.deliver(
        notification.id,
        max_attempts=3,
    )

    assert result is NotificationStatus.FAILED
    repository.get_delivery_context.assert_not_awaited()
    sender.send.assert_not_awaited()
    session.commit.assert_awaited_once()
