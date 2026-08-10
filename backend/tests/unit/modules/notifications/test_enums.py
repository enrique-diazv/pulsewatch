from app.modules.notifications.enums import (
    NotificationStatus,
    NotificationType,
)


def test_notification_types_use_stable_values() -> None:
    assert NotificationType.INCIDENT_OPENED.value == ("INCIDENT_OPENED")
    assert NotificationType.INCIDENT_RESOLVED.value == ("INCIDENT_RESOLVED")


def test_notification_statuses_use_stable_values() -> None:
    assert NotificationStatus.PENDING.value == "PENDING"
    assert NotificationStatus.SENT.value == "SENT"
    assert NotificationStatus.FAILED.value == "FAILED"
