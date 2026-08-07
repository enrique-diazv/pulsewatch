from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from app.core.config import Settings
from app.security.tokens import (
    InvalidAccessTokenError,
    create_access_token,
    decode_access_token,
)


def create_test_settings(secret: str) -> Settings:
    return Settings(
        _env_file=None,
        database_password="test-password",
        jwt_secret_key=secret,
        access_token_expire_minutes=15,
    )


def test_access_token_round_trip() -> None:
    settings = create_test_settings(
        "first-test-jwt-secret-key-over-32-characters",
    )
    user_id = uuid4()

    token = create_access_token(user_id, settings=settings)
    decoded_user_id = decode_access_token(token, settings=settings)

    assert decoded_user_id == user_id


def test_access_token_rejects_incorrect_signature() -> None:
    signing_settings = create_test_settings(
        "signing-test-jwt-secret-key-over-32-characters",
    )
    verifying_settings = create_test_settings(
        "different-test-jwt-secret-key-over-32-characters",
    )
    token = create_access_token(
        uuid4(),
        settings=signing_settings,
    )

    with pytest.raises(InvalidAccessTokenError):
        decode_access_token(token, settings=verifying_settings)


def test_access_token_rejects_expired_token() -> None:
    settings = create_test_settings(
        "expired-test-jwt-secret-key-over-32-characters",
    )
    issued_at = datetime.now(UTC) - timedelta(minutes=16)
    token = create_access_token(
        uuid4(),
        settings=settings,
        now=issued_at,
    )

    with pytest.raises(InvalidAccessTokenError):
        decode_access_token(token, settings=settings)
