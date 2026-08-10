from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.config import Settings
from app.integrations.email import (
    LogEmailSender,
    SmtpEmailSender,
    create_email_sender,
)
from app.modules.notifications.email import EmailMessage


def create_settings(**overrides: object) -> Settings:
    values = {
        "database_password": "test-password",
        "jwt_secret_key": ("test-jwt-secret-key-with-at-least-32-characters"),
        **overrides,
    }

    return Settings(
        _env_file=None,
        **values,
    )


def create_message() -> EmailMessage:
    return EmailMessage(
        recipient="owner@example.com",
        subject="PulseWatch alert",
        text_body="Production API is down.",
    )


def test_factory_uses_log_sender_by_default() -> None:
    sender = create_email_sender(create_settings())

    assert isinstance(sender, LogEmailSender)


def test_smtp_sender_rejects_conflicting_tls_modes() -> None:
    settings = create_settings(
        email_delivery_mode="smtp",
        smtp_use_tls=True,
        smtp_start_tls=True,
    )

    with pytest.raises(
        ValueError,
        match="cannot both be enabled",
    ):
        SmtpEmailSender(settings)


def test_smtp_sender_builds_and_sends_message() -> None:
    settings = create_settings(
        email_delivery_mode="smtp",
        email_from_address="alerts@example.com",
        smtp_host="smtp.example.com",
        smtp_port=587,
        smtp_username="smtp-user",
        smtp_password="smtp-password",
        smtp_start_tls=True,
    )
    sender = SmtpEmailSender(settings)
    smtp_client = MagicMock()

    with patch(
        "app.integrations.email.smtplib.SMTP",
    ) as smtp_class:
        smtp_class.return_value.__enter__.return_value = smtp_client

        sender._send_sync(create_message())

    smtp_class.assert_called_once_with(
        "smtp.example.com",
        587,
        timeout=30,
    )
    smtp_client.starttls.assert_called_once()
    smtp_client.login.assert_called_once_with(
        "smtp-user",
        "smtp-password",
    )
    smtp_client.send_message.assert_called_once()

    sent_message = smtp_client.send_message.call_args.args[0]
    assert sent_message["From"] == "alerts@example.com"
    assert sent_message["To"] == "owner@example.com"
    assert sent_message["Subject"] == "PulseWatch alert"
    assert "Production API is down." in (sent_message.get_content())


@pytest.mark.anyio
async def test_smtp_sender_runs_blocking_io_in_thread() -> None:
    sender = SmtpEmailSender(create_settings(email_delivery_mode="smtp"))
    message = create_message()

    with patch(
        "app.integrations.email.asyncio.to_thread",
        new_callable=AsyncMock,
    ) as to_thread:
        await sender.send(message)

    to_thread.assert_awaited_once_with(
        sender._send_sync,
        message,
    )
