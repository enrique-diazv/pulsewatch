import pytest

from app.core.config import Settings


def test_cors_uses_local_frontend_by_default(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("CORS_ALLOWED_ORIGINS", raising=False)

    settings = Settings(_env_file=None)

    assert settings.cors_allowed_origins == ("http://localhost:5173",)


def test_cors_origins_can_be_configured(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(
        "CORS_ALLOWED_ORIGINS",
        '["https://app.example.test"]',
    )

    settings = Settings(_env_file=None)

    assert settings.cors_allowed_origins == ("https://app.example.test",)
