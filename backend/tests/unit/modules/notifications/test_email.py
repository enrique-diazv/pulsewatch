from datetime import UTC, datetime

import pytest

from app.modules.notifications.email import (
    build_incident_email,
)
from app.modules.notifications.enums import NotificationType

STARTED_AT = datetime(2026, 8, 9, 18, 0, tzinfo=UTC)
RESOLVED_AT = datetime(2026, 8, 9, 18, 8, tzinfo=UTC)


def test_build_incident_opened_email() -> None:
    message = build_incident_email(
        notification_type=NotificationType.INCIDENT_OPENED,
        recipient="owner@example.com",
        monitor_name="Production API",
        monitor_url="https://api.example.com/health",
        failure_reason="Request timed out",
        started_at=STARTED_AT,
        resolved_at=None,
    )

    assert message.recipient == "owner@example.com"
    assert message.subject == ("PulseWatch alert: Production API is down")
    assert "Request timed out" in message.text_body
    assert "2026-08-09 18:00:00 UTC" in message.text_body


def test_build_incident_resolved_email() -> None:
    message = build_incident_email(
        notification_type=(NotificationType.INCIDENT_RESOLVED),
        recipient="owner@example.com",
        monitor_name="Production API",
        monitor_url="https://api.example.com/health",
        failure_reason="Request timed out",
        started_at=STARTED_AT,
        resolved_at=RESOLVED_AT,
    )

    assert message.subject == ("PulseWatch recovery: Production API is up")
    assert "2026-08-09 18:08:00 UTC" in message.text_body


def test_resolved_email_requires_resolution_timestamp() -> None:
    with pytest.raises(
        ValueError,
        match="requires resolved_at",
    ):
        build_incident_email(
            notification_type=(NotificationType.INCIDENT_RESOLVED),
            recipient="owner@example.com",
            monitor_name="Production API",
            monitor_url="https://api.example.com/health",
            failure_reason="Request timed out",
            started_at=STARTED_AT,
            resolved_at=None,
        )
