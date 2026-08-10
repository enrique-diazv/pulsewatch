from collections.abc import AsyncIterator
from hashlib import sha256
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from fastapi.testclient import TestClient
from redis.asyncio import Redis as AsyncRedis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.database.models.user import User
from app.database.session import get_database_session
from app.main import app
from app.modules.auth.dependencies import get_current_user


def create_redis_mock() -> MagicMock:
    redis_client = MagicMock(spec=AsyncRedis)
    redis_client.set = AsyncMock(return_value=True)
    redis_client.aclose = AsyncMock()

    return redis_client


def test_issue_realtime_ticket_for_authenticated_user() -> None:
    current_user = User(
        id=uuid4(),
        email="owner@example.com",
        password_hash="hashed-password",
    )
    redis_client = create_redis_mock()
    settings = Settings(
        _env_file=None,
        database_password="test-password",
        jwt_secret_key=("test-jwt-secret-key-with-at-least-32-characters"),
        realtime_ticket_ttl_seconds=45,
    )
    app.dependency_overrides[get_current_user] = lambda: current_user

    try:
        with (
            patch(
                "app.api.v1.endpoints.realtime.create_async_redis_client",
                return_value=redis_client,
            ),
            patch(
                "app.api.v1.endpoints.realtime.get_settings",
                return_value=settings,
            ),
            TestClient(app) as client,
        ):
            response = client.post("/api/v1/realtime/ticket")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 201
    payload = response.json()
    assert payload["expires_in"] == 45
    assert len(payload["ticket"]) >= 32

    ticket_hash = sha256(payload["ticket"].encode("utf-8")).hexdigest()
    redis_client.set.assert_awaited_once_with(
        f"realtime-ticket:{ticket_hash}",
        str(current_user.id),
        ex=45,
        nx=True,
    )
    redis_client.aclose.assert_awaited_once()


def test_realtime_ticket_requires_authentication() -> None:
    database_session = AsyncMock(spec=AsyncSession)
    redis_client = create_redis_mock()

    async def override_database_session() -> AsyncIterator[AsyncSession]:
        yield database_session

    app.dependency_overrides[get_database_session] = override_database_session

    try:
        with (
            patch(
                "app.api.v1.endpoints.realtime.create_async_redis_client",
                return_value=redis_client,
            ),
            TestClient(app) as client,
        ):
            response = client.post("/api/v1/realtime/ticket")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 401
