from collections.abc import AsyncIterator, Iterator
from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.user import User
from app.database.session import get_database_session
from app.main import app
from app.modules.auth.dependencies import get_current_user
from app.modules.auth.exceptions import (
    EmailAlreadyRegisteredError,
    InvalidCredentialsError,
    InvalidRefreshTokenError,
)
from app.modules.auth.refresh_token_service import RefreshTokenRotation


@pytest.fixture
def database_session() -> AsyncMock:
    return AsyncMock(spec=AsyncSession)


@pytest.fixture
def client(database_session: AsyncMock) -> Iterator[TestClient]:
    async def override_database_session() -> AsyncIterator[AsyncSession]:
        yield database_session

    app.dependency_overrides[get_database_session] = override_database_session

    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.clear()


def test_register_returns_created_user(client: TestClient) -> None:
    user_id = uuid4()
    timestamp = datetime(2026, 8, 7, tzinfo=UTC)
    user = User(
        id=user_id,
        email="user@example.com",
        password_hash="must-not-be-exposed",
        is_verified=False,
        created_at=timestamp,
        updated_at=timestamp,
    )

    with patch(
        "app.api.v1.endpoints.auth.AuthService.register",
        new_callable=AsyncMock,
        return_value=user,
    ) as register:
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "user@example.com",
                "password": "correct horse battery staple",
            },
        )

    assert response.status_code == 201
    assert response.json()["id"] == str(user_id)
    assert response.json()["email"] == "user@example.com"
    assert response.json()["is_verified"] is False
    assert "password_hash" not in response.json()
    register.assert_awaited_once()


def test_register_returns_conflict_for_existing_email(
    client: TestClient,
) -> None:
    with patch(
        "app.api.v1.endpoints.auth.AuthService.register",
        new_callable=AsyncMock,
        side_effect=EmailAlreadyRegisteredError,
    ):
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "user@example.com",
                "password": "correct horse battery staple",
            },
        )

    assert response.status_code == 409
    assert response.json() == {
        "detail": "Email is already registered",
    }


def test_register_rejects_invalid_input(client: TestClient) -> None:
    with patch(
        "app.api.v1.endpoints.auth.AuthService.register",
        new_callable=AsyncMock,
    ) as register:
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "not-an-email",
                "password": "short",
            },
        )

    assert response.status_code == 422
    register.assert_not_awaited()


def test_login_returns_access_token(client: TestClient) -> None:
    user = User(
        id=uuid4(),
        email="user@example.com",
        password_hash="hashed-password",
    )

    with (
        patch(
            "app.api.v1.endpoints.auth.AuthService.authenticate",
            new_callable=AsyncMock,
            return_value=user,
        ) as authenticate,
        patch(
            "app.api.v1.endpoints.auth.create_access_token",
            return_value="signed-access-token",
        ) as token_creator,
        patch(
            "app.api.v1.endpoints.auth.RefreshTokenService.issue",
            new_callable=AsyncMock,
            return_value="raw-refresh-token",
        ) as refresh_issuer,
    ):
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "user@example.com",
                "password": "existing-password",
            },
        )

    assert response.status_code == 200
    assert response.json() == {
        "access_token": "signed-access-token",
        "token_type": "bearer",
        "expires_in": 900,
    }
    authenticate.assert_awaited_once()
    token_creator.assert_called_once_with(user.id)
    refresh_issuer.assert_awaited_once_with(user.id)

    cookie = response.headers["set-cookie"]
    assert "pulsewatch_refresh_token=raw-refresh-token" in cookie
    assert "HttpOnly" in cookie
    assert "Path=/api/v1/auth" in cookie
    assert "SameSite=lax" in cookie


def test_login_returns_unauthorized_for_invalid_credentials(
    client: TestClient,
) -> None:
    with patch(
        "app.api.v1.endpoints.auth.AuthService.authenticate",
        new_callable=AsyncMock,
        side_effect=InvalidCredentialsError,
    ):
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "user@example.com",
                "password": "incorrect-password",
            },
        )

    assert response.status_code == 401
    assert response.json() == {
        "detail": "Invalid email or password",
    }
    assert response.headers["www-authenticate"] == "Bearer"


def test_login_rejects_empty_password(client: TestClient) -> None:
    with patch(
        "app.api.v1.endpoints.auth.AuthService.authenticate",
        new_callable=AsyncMock,
    ) as authenticate:
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "user@example.com",
                "password": "",
            },
        )

    assert response.status_code == 422
    authenticate.assert_not_awaited()


def test_me_returns_authenticated_user(client: TestClient) -> None:
    user_id = uuid4()
    timestamp = datetime(2026, 8, 7, tzinfo=UTC)
    user = User(
        id=user_id,
        email="user@example.com",
        password_hash="must-not-be-exposed",
        is_verified=False,
        created_at=timestamp,
        updated_at=timestamp,
    )

    app.dependency_overrides[get_current_user] = lambda: user

    try:
        response = client.get("/api/v1/auth/me")
    finally:
        app.dependency_overrides.pop(get_current_user, None)

    assert response.status_code == 200
    assert response.json()["id"] == str(user_id)
    assert response.json()["email"] == "user@example.com"
    assert "password_hash" not in response.json()


def test_me_requires_access_token(client: TestClient) -> None:
    response = client.get("/api/v1/auth/me")

    assert response.status_code == 401
    assert response.json() == {
        "detail": "Invalid or missing access token",
    }
    assert response.headers["www-authenticate"] == "Bearer"


def test_refresh_rotates_cookie_and_returns_access_token(
    client: TestClient,
) -> None:
    user_id = uuid4()
    client.cookies.set(
        "pulsewatch_refresh_token",
        "old-raw-refresh-token",
    )

    with (
        patch(
            "app.api.v1.endpoints.auth.RefreshTokenService.rotate",
            new_callable=AsyncMock,
            return_value=RefreshTokenRotation(
                user_id=user_id,
                token="new-raw-refresh-token",
            ),
        ) as rotate,
        patch(
            "app.api.v1.endpoints.auth.create_access_token",
            return_value="new-access-token",
        ),
    ):
        response = client.post("/api/v1/auth/refresh")

    assert response.status_code == 200
    assert response.json() == {
        "access_token": "new-access-token",
        "token_type": "bearer",
        "expires_in": 900,
    }
    rotate.assert_awaited_once_with("old-raw-refresh-token")

    cookie = response.headers["set-cookie"]
    assert "pulsewatch_refresh_token=new-raw-refresh-token" in cookie
    assert "HttpOnly" in cookie


def test_refresh_rejects_missing_cookie(client: TestClient) -> None:
    with patch(
        "app.api.v1.endpoints.auth.RefreshTokenService.rotate",
        new_callable=AsyncMock,
    ) as rotate:
        response = client.post("/api/v1/auth/refresh")

    assert response.status_code == 401
    assert response.json() == {
        "detail": "Invalid or expired refresh token",
    }
    rotate.assert_not_awaited()


def test_refresh_rejects_invalid_cookie(client: TestClient) -> None:
    client.cookies.set(
        "pulsewatch_refresh_token",
        "invalid-refresh-token",
    )

    with patch(
        "app.api.v1.endpoints.auth.RefreshTokenService.rotate",
        new_callable=AsyncMock,
        side_effect=InvalidRefreshTokenError,
    ):
        response = client.post("/api/v1/auth/refresh")

    assert response.status_code == 401
    assert response.json() == {
        "detail": "Invalid or expired refresh token",
    }
    assert "Max-Age=0" in response.headers["set-cookie"]


def test_logout_revokes_token_and_clears_cookie(
    client: TestClient,
) -> None:
    client.cookies.set(
        "pulsewatch_refresh_token",
        "raw-refresh-token",
    )

    with patch(
        "app.api.v1.endpoints.auth.RefreshTokenService.revoke",
        new_callable=AsyncMock,
        return_value=True,
    ) as revoke:
        response = client.post("/api/v1/auth/logout")

    assert response.status_code == 204
    assert response.content == b""
    revoke.assert_awaited_once_with("raw-refresh-token")
    assert "Max-Age=0" in response.headers["set-cookie"]


def test_logout_without_cookie_is_idempotent(
    client: TestClient,
) -> None:
    with patch(
        "app.api.v1.endpoints.auth.RefreshTokenService.revoke",
        new_callable=AsyncMock,
    ) as revoke:
        response = client.post("/api/v1/auth/logout")

    assert response.status_code == 204
    assert response.content == b""
    revoke.assert_not_awaited()
    assert "Max-Age=0" in response.headers["set-cookie"]
