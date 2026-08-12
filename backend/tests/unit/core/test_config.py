import pytest

from app.core.config import Settings

SETTING_VARIABLES = (
    "APP_NAME",
    "APP_VERSION",
    "ENVIRONMENT",
    "DASHBOARD_CACHE_TTL_SECONDS",
    "DEBUG",
    "LOG_LEVEL",
    "DATABASE_HOST",
    "DATABASE_PORT",
    "DATABASE_NAME",
    "DATABASE_USER",
    "DATABASE_PASSWORD",
    "JWT_SECRET_KEY",
    "ACCESS_TOKEN_EXPIRE_MINUTES",
    "REFRESH_TOKEN_EXPIRE_DAYS",
    "REDIS_URL",
    "MANUAL_CHECK_COOLDOWN_SECONDS",
    "SCHEDULER_POLL_INTERVAL_SECONDS",
    "SCHEDULER_BATCH_SIZE",
    "NOTIFICATION_DISPATCH_INTERVAL_SECONDS",
    "NOTIFICATION_BATCH_SIZE",
    "NOTIFICATION_MAX_ATTEMPTS",
    "EMAIL_DELIVERY_MODE",
    "EMAIL_FROM_ADDRESS",
    "SMTP_HOST",
    "SMTP_PORT",
    "SMTP_USERNAME",
    "SMTP_PASSWORD",
    "SMTP_USE_TLS",
    "SMTP_START_TLS",
    "REALTIME_TICKET_TTL_SECONDS",
    "RAW_CHECK_RETENTION_DAYS",
    "RETENTION_BATCH_SIZE",
)


def test_settings_use_default_values(monkeypatch: pytest.MonkeyPatch) -> None:
    for variable in SETTING_VARIABLES:
        monkeypatch.delenv(variable, raising=False)

    monkeypatch.setenv("DATABASE_PASSWORD", "test-password")
    monkeypatch.setenv(
        "JWT_SECRET_KEY",
        "test-jwt-secret-key-with-at-least-32-characters",
    )

    settings = Settings(_env_file=None)
    assert settings.manual_check_cooldown_seconds == 10
    assert settings.app_name == "PulseWatch API"
    assert settings.app_version == "0.1.0"
    assert settings.environment == "development"
    assert settings.debug is False
    assert settings.log_level == "INFO"
    assert settings.database_host == "127.0.0.1"
    assert settings.database_port == 5432
    assert settings.database_name == "pulsewatch"
    assert settings.database_user == "pulsewatch_app"
    assert settings.database_password.get_secret_value() == "test-password"
    assert str(settings.database_password) == "**********"
    assert settings.jwt_secret_key.get_secret_value() == (
        "test-jwt-secret-key-with-at-least-32-characters"
    )
    assert str(settings.jwt_secret_key) == "**********"
    assert settings.access_token_expire_minutes == 15
    assert settings.refresh_token_expire_days == 30
    assert str(settings.redis_url) == "redis://127.0.0.1:6379/0"
    assert settings.scheduler_poll_interval_seconds == 10
    assert settings.scheduler_batch_size == 100
    assert settings.notification_dispatch_interval_seconds == 15
    assert settings.notification_batch_size == 100
    assert settings.notification_max_attempts == 3
    assert settings.email_delivery_mode == "log"
    assert settings.email_from_address == "alerts@pulsewatch.local"
    assert settings.smtp_host == "127.0.0.1"
    assert settings.smtp_port == 1025
    assert settings.smtp_username is None
    assert settings.smtp_password is None
    assert settings.smtp_use_tls is False
    assert settings.smtp_start_tls is False
    assert settings.realtime_ticket_ttl_seconds == 30
    assert settings.dashboard_cache_ttl_seconds == 30
    assert settings.raw_check_retention_days == 30
    assert settings.retention_batch_size == 10_000


def test_settings_read_environment_variables(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("APP_NAME", "PulseWatch Test API")
    monkeypatch.setenv("APP_VERSION", "9.9.9")
    monkeypatch.setenv("ENVIRONMENT", "testing")
    monkeypatch.setenv("DEBUG", "true")
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")
    monkeypatch.setenv("DATABASE_HOST", "database.example.test")
    monkeypatch.setenv("DATABASE_PORT", "55432")
    monkeypatch.setenv("DATABASE_NAME", "pulsewatch_test")
    monkeypatch.setenv("DATABASE_USER", "pulsewatch_test_user")
    monkeypatch.setenv("DATABASE_PASSWORD", "another-test-password")
    monkeypatch.setenv(
        "JWT_SECRET_KEY",
        "another-test-jwt-secret-key-over-32-characters",
    )
    monkeypatch.setenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30")
    monkeypatch.setenv("REFRESH_TOKEN_EXPIRE_DAYS", "45")
    monkeypatch.setenv(
        "REDIS_URL",
        "redis://cache.example.test:6380/2",
    )
    monkeypatch.setenv(
        "MANUAL_CHECK_COOLDOWN_SECONDS",
        "30",
    )
    monkeypatch.setenv(
        "SCHEDULER_POLL_INTERVAL_SECONDS",
        "5",
    )
    monkeypatch.setenv(
        "SCHEDULER_BATCH_SIZE",
        "250",
    )
    monkeypatch.setenv(
        "NOTIFICATION_DISPATCH_INTERVAL_SECONDS",
        "30",
    )
    monkeypatch.setenv("NOTIFICATION_BATCH_SIZE", "50")
    monkeypatch.setenv("NOTIFICATION_MAX_ATTEMPTS", "5")
    monkeypatch.setenv("EMAIL_DELIVERY_MODE", "smtp")
    monkeypatch.setenv(
        "EMAIL_FROM_ADDRESS",
        "alerts@example.com",
    )
    monkeypatch.setenv("SMTP_HOST", "smtp.example.com")
    monkeypatch.setenv("SMTP_PORT", "465")
    monkeypatch.setenv("SMTP_USERNAME", "smtp-user")
    monkeypatch.setenv("SMTP_PASSWORD", "smtp-password")
    monkeypatch.setenv("SMTP_USE_TLS", "true")
    monkeypatch.setenv("SMTP_START_TLS", "false")
    monkeypatch.setenv(
        "REALTIME_TICKET_TTL_SECONDS",
        "45",
    )
    monkeypatch.setenv(
        "DASHBOARD_CACHE_TTL_SECONDS",
        "45",
    )
    monkeypatch.setenv(
        "RAW_CHECK_RETENTION_DAYS",
        "45",
    )
    monkeypatch.setenv(
        "RETENTION_BATCH_SIZE",
        "5000",
    )
    settings = Settings(_env_file=None)

    assert settings.app_name == "PulseWatch Test API"
    assert settings.app_version == "9.9.9"
    assert settings.environment == "testing"
    assert settings.debug is True
    assert settings.log_level == "DEBUG"
    assert settings.database_host == "database.example.test"
    assert settings.database_port == 55432
    assert settings.database_name == "pulsewatch_test"
    assert settings.database_user == "pulsewatch_test_user"
    assert settings.database_password.get_secret_value() == ("another-test-password")
    assert settings.jwt_secret_key.get_secret_value() == (
        "another-test-jwt-secret-key-over-32-characters"
    )
    assert settings.access_token_expire_minutes == 30
    assert settings.refresh_token_expire_days == 45
    assert str(settings.redis_url) == "redis://cache.example.test:6380/2"
    assert settings.manual_check_cooldown_seconds == 30
    assert settings.scheduler_poll_interval_seconds == 5
    assert settings.scheduler_batch_size == 250
    assert settings.notification_dispatch_interval_seconds == 30
    assert settings.notification_batch_size == 50
    assert settings.notification_max_attempts == 5
    assert settings.email_delivery_mode == "smtp"
    assert settings.email_from_address == "alerts@example.com"
    assert settings.smtp_host == "smtp.example.com"
    assert settings.smtp_port == 465
    assert settings.smtp_username == "smtp-user"
    assert (
        settings.smtp_password is not None
        and settings.smtp_password.get_secret_value() == "smtp-password"
    )
    assert settings.smtp_use_tls is True
    assert settings.smtp_start_tls is False
    assert settings.realtime_ticket_ttl_seconds == 45
    assert settings.dashboard_cache_ttl_seconds == 45
    assert settings.raw_check_retention_days == 45
    assert settings.retention_batch_size == 5000
