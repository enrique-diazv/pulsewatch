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
from app.modules.auth.exceptions import EmailAlreadyRegisteredError


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
