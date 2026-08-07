import pytest

from app.core.config import Settings

SETTING_VARIABLES = (
    "APP_NAME",
    "APP_VERSION",
    "ENVIRONMENT",
    "DEBUG",
    "DATABASE_HOST",
    "DATABASE_PORT",
    "DATABASE_NAME",
    "DATABASE_USER",
    "DATABASE_PASSWORD",
)


def test_settings_use_default_values(monkeypatch: pytest.MonkeyPatch) -> None:
    for variable in SETTING_VARIABLES:
        monkeypatch.delenv(variable, raising=False)

    monkeypatch.setenv("DATABASE_PASSWORD", "test-password")

    settings = Settings(_env_file=None)

    assert settings.app_name == "PulseWatch API"
    assert settings.app_version == "0.1.0"
    assert settings.environment == "development"
    assert settings.debug is False
    assert settings.database_host == "127.0.0.1"
    assert settings.database_port == 5432
    assert settings.database_name == "pulsewatch"
    assert settings.database_user == "pulsewatch_app"
    assert settings.database_password.get_secret_value() == "test-password"
    assert str(settings.database_password) == "**********"


def test_settings_read_environment_variables(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("APP_NAME", "PulseWatch Test API")
    monkeypatch.setenv("APP_VERSION", "9.9.9")
    monkeypatch.setenv("ENVIRONMENT", "testing")
    monkeypatch.setenv("DEBUG", "true")
    monkeypatch.setenv("DATABASE_HOST", "database.example.test")
    monkeypatch.setenv("DATABASE_PORT", "55432")
    monkeypatch.setenv("DATABASE_NAME", "pulsewatch_test")
    monkeypatch.setenv("DATABASE_USER", "pulsewatch_test_user")
    monkeypatch.setenv("DATABASE_PASSWORD", "another-test-password")

    settings = Settings(_env_file=None)

    assert settings.app_name == "PulseWatch Test API"
    assert settings.app_version == "9.9.9"
    assert settings.environment == "testing"
    assert settings.debug is True
    assert settings.database_host == "database.example.test"
    assert settings.database_port == 55432
    assert settings.database_name == "pulsewatch_test"
    assert settings.database_user == "pulsewatch_test_user"
    assert settings.database_password.get_secret_value() == "another-test-password"
