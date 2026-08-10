from dataclasses import dataclass
from datetime import UTC, datetime

from app.modules.notifications.enums import NotificationType


@dataclass(frozen=True, slots=True)
class EmailMessage:
    recipient: str
    subject: str
    text_body: str


def format_timestamp(value: datetime) -> str:
    return value.astimezone(UTC).strftime("%Y-%m-%d %H:%M:%S UTC")


def build_incident_email(
    *,
    notification_type: NotificationType,
    recipient: str,
    monitor_name: str,
    monitor_url: str,
    failure_reason: str,
    started_at: datetime,
    resolved_at: datetime | None,
) -> EmailMessage:
    if notification_type is NotificationType.INCIDENT_OPENED:
        subject = f"PulseWatch alert: {monitor_name} is down"
        text_body = "\n".join(
            (
                f"PulseWatch detected that {monitor_name} is down.",
                "",
                f"Monitor: {monitor_name}",
                f"URL: {monitor_url}",
                f"Detected at: {format_timestamp(started_at)}",
                f"Reason: {failure_reason}",
            )
        )

        return EmailMessage(
            recipient=recipient,
            subject=subject,
            text_body=text_body,
        )

    if resolved_at is None:
        raise ValueError("Resolved notification requires resolved_at")

    subject = f"PulseWatch recovery: {monitor_name} is up"
    text_body = "\n".join(
        (
            f"PulseWatch detected that {monitor_name} recovered.",
            "",
            f"Monitor: {monitor_name}",
            f"URL: {monitor_url}",
            f"Incident started: {format_timestamp(started_at)}",
            f"Recovered at: {format_timestamp(resolved_at)}",
            f"Original reason: {failure_reason}",
        )
    )

    return EmailMessage(
        recipient=recipient,
        subject=subject,
        text_body=text_body,
    )
