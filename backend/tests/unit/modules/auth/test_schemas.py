from datetime import UTC, datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.database.models.user import User
from app.modules.auth.schemas import LoginRequest, RegisterRequest, UserResponse


def test_register_request_accepts_valid_credentials() -> None:
    request = RegisterRequest(
        email="user@example.com",
        password="correct horse battery staple",
    )

    assert str(request.email) == "user@example.com"
    assert request.password == "correct horse battery staple"


def test_register_request_rejects_invalid_email() -> None:
    with pytest.raises(ValidationError):
        RegisterRequest(
            email="not-an-email",
            password="correct horse battery staple",
        )


def test_register_request_requires_at_least_six_characters() -> None:
    with pytest.raises(ValidationError):
        RegisterRequest(
            email="user@example.com",
            password="short",
        )


def test_register_request_does_not_require_character_composition() -> None:
    request = RegisterRequest(
        email="user@example.com",
        password="long passphrase",
    )

    assert request.password == "long passphrase"


def test_user_response_excludes_password_hash() -> None:
    timestamp = datetime.now(UTC)
    user = User(
        id=uuid4(),
        email="user@example.com",
        password_hash="must-not-be-exposed",
        is_verified=False,
        created_at=timestamp,
        updated_at=timestamp,
    )

    response = UserResponse.model_validate(user)
    response_data = response.model_dump()

    assert response_data["email"] == "user@example.com"
    assert response_data["is_verified"] is False
    assert "password_hash" not in response_data


def test_login_request_accepts_existing_password() -> None:
    request = LoginRequest(
        email="user@example.com",
        password="existing-password",
    )

    assert str(request.email) == "user@example.com"
    assert request.password == "existing-password"


def test_login_request_rejects_empty_password() -> None:
    with pytest.raises(ValidationError):
        LoginRequest(
            email="user@example.com",
            password="",
        )
