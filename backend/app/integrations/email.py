import asyncio
import smtplib
from email.message import EmailMessage as StandardEmailMessage
from typing import Protocol

from app.core.config import Settings, get_settings
from app.core.logging import get_logger
from app.modules.notifications.email import EmailMessage

logger = get_logger(__name__)


class EmailSender(Protocol):
    async def send(self, message: EmailMessage) -> None: ...


class LogEmailSender:
    async def send(self, message: EmailMessage) -> None:
        recipient_domain = message.recipient.rpartition("@")[2]

        logger.info(
            "email_delivery_simulated",
            extra={
                "recipient_domain": recipient_domain,
                "subject": message.subject,
            },
        )


class SmtpEmailSender:
    def __init__(self, settings: Settings) -> None:
        if settings.smtp_use_tls and settings.smtp_start_tls:
            raise ValueError("SMTP_USE_TLS and SMTP_START_TLS cannot both be enabled")

        if settings.smtp_username is not None and settings.smtp_password is None:
            raise ValueError("SMTP_PASSWORD is required with SMTP_USERNAME")

        self.settings = settings

    async def send(self, message: EmailMessage) -> None:
        await asyncio.to_thread(
            self._send_sync,
            message,
        )

    def _send_sync(self, message: EmailMessage) -> None:
        email_message = StandardEmailMessage()
        email_message["From"] = self.settings.email_from_address
        email_message["To"] = message.recipient
        email_message["Subject"] = message.subject
        email_message.set_content(message.text_body)

        smtp_class = smtplib.SMTP_SSL if self.settings.smtp_use_tls else smtplib.SMTP

        with smtp_class(
            self.settings.smtp_host,
            self.settings.smtp_port,
            timeout=30,
        ) as client:
            if self.settings.smtp_start_tls:
                client.starttls()

            if self.settings.smtp_username is not None:
                smtp_password = self.settings.smtp_password

                if smtp_password is None:
                    raise RuntimeError("SMTP password unexpectedly missing")

                client.login(
                    self.settings.smtp_username,
                    smtp_password.get_secret_value(),
                )

            client.send_message(email_message)


def create_email_sender(
    settings: Settings | None = None,
) -> EmailSender:
    resolved_settings = settings or get_settings()

    if resolved_settings.email_delivery_mode == "log":
        return LogEmailSender()

    return SmtpEmailSender(resolved_settings)
