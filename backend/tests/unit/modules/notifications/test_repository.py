from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from sqlalchemy.dialects import postgresql
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.notification import Notification
from app.modules.notifications.enums import NotificationType
from app.modules.notifications.repository import (
    NotificationRepository,
)


def create_notification() -> Notification:
    return Notification(
        user_id=uuid4(),
        incident_id=uuid4(),
        type=NotificationType.INCIDENT_OPENED,
    )


@pytest.mark.anyio
async def test_add_flushes_notification() -> None:
    session = AsyncMock(spec=AsyncSession)
    repository = NotificationRepository(session)
    notification = create_notification()

    added_notification = await repository.add(notification)

    assert added_notification is notification
    session.add.assert_called_once_with(notification)
    session.flush.assert_awaited_once()


@pytest.mark.anyio
async def test_list_deliverable_ids_limits_retries() -> None:
    session = AsyncMock(spec=AsyncSession)
    result = MagicMock()
    notification_ids = [uuid4(), uuid4()]
    result.scalars.return_value.all.return_value = notification_ids
    session.execute.return_value = result
    repository = NotificationRepository(session)

    found_ids = await repository.list_deliverable_ids(
        limit=100,
        max_attempts=3,
    )

    assert found_ids == notification_ids

    statement = session.execute.await_args.args[0]
    sql = str(
        statement.compile(
            dialect=postgresql.dialect(),
            compile_kwargs={"literal_binds": True},
        )
    )

    assert "notifications.status IN" in sql
    assert "notifications.attempt_count < 3" in sql
    assert ("ORDER BY notifications.created_at ASC, notifications.id ASC") in sql
    assert "LIMIT 100" in sql


@pytest.mark.anyio
async def test_get_for_update_locks_notification() -> None:
    session = AsyncMock(spec=AsyncSession)
    result = MagicMock()
    notification = create_notification()
    result.scalar_one_or_none.return_value = notification
    session.execute.return_value = result
    repository = NotificationRepository(session)

    found_notification = await repository.get_for_update(
        notification.id,
    )

    assert found_notification is notification

    statement = session.execute.await_args.args[0]
    sql = str(
        statement.compile(
            dialect=postgresql.dialect(),
            compile_kwargs={"literal_binds": True},
        )
    )

    assert "FOR UPDATE" in sql


@pytest.mark.anyio
async def test_get_delivery_context_joins_owned_resources() -> None:
    session = AsyncMock(spec=AsyncSession)
    result = MagicMock()
    started_at = datetime(2026, 8, 9, 18, 0, tzinfo=UTC)
    resolved_at = datetime(
        2026,
        8,
        9,
        18,
        8,
        tzinfo=UTC,
    )
    result.one_or_none.return_value = SimpleNamespace(
        recipient_email="owner@example.com",
        monitor_name="Production API",
        monitor_url="https://api.example.com/health",
        failure_reason="Request timed out",
        started_at=started_at,
        resolved_at=resolved_at,
    )
    session.execute.return_value = result
    repository = NotificationRepository(session)
    notification_id = uuid4()

    context = await repository.get_delivery_context(notification_id)

    assert context is not None
    assert context.recipient_email == "owner@example.com"
    assert context.monitor_name == "Production API"
    assert context.monitor_url == "https://api.example.com/health"
    assert context.failure_reason == "Request timed out"
    assert context.started_at == started_at
    assert context.resolved_at == resolved_at

    statement = session.execute.await_args.args[0]
    sql = str(
        statement.compile(
            dialect=postgresql.dialect(),
            compile_kwargs={"literal_binds": True},
        )
    )

    assert "JOIN users" in sql
    assert "JOIN incidents" in sql
    assert "JOIN monitors" in sql
    assert f"notifications.id = '{notification_id}'" in sql
