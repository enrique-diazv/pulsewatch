import pytest

from app.core.config import Settings

SETTING_VARIABLES = (
    "APP_NAME",
    "APP_VERSION",
    "ENVIRONMENT",
    "DEBUG",
)


def test_settings_use_default_values(monkeypatch: pytest.MonkeyPatch) -> None:
    for variable in SETTING_VARIABLES:
        monkeypatch.delenv(variable, raising=False)

    settings = Settings(_env_file=None)

    assert settings.app_name == "PulseWatch API"
    assert settings.app_version == "0.1.0"
    assert settings.environment == "development"
    assert settings.debug is False


def test_settings_read_environment_variables(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("APP_NAME", "PulseWatch Test API")
    monkeypatch.setenv("APP_VERSION", "9.9.9")
    monkeypatch.setenv("ENVIRONMENT", "testing")
    monkeypatch.setenv("DEBUG", "true")

    settings = Settings(_env_file=None)

    assert settings.app_name == "PulseWatch Test API"
    assert settings.app_version == "9.9.9"
    assert settings.environment == "testing"
    assert settings.debug is True
