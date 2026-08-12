from collections.abc import AsyncIterator, Iterator
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from redis.asyncio import Redis as AsyncRedis
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.endpoints.dashboard import get_dashboard_redis
from app.database.models.user import User
from app.database.session import get_database_session
from app.main import app
from app.modules.auth.dependencies import get_current_user
from app.modules.dashboard.schemas import DashboardSummary


@pytest.fixture
def current_user() -> User:
    return User(
        id=uuid4(),
        email="owner@example.com",
        password_hash="hashed-password",
    )


@pytest.fixture
def database_session() -> AsyncMock:
    return AsyncMock(spec=AsyncSession)


@pytest.fixture
def redis_client() -> MagicMock:
    return MagicMock(spec=AsyncRedis)


@pytest.fixture
def client(
    current_user: User,
    database_session: AsyncMock,
    redis_client: MagicMock,
) -> Iterator[TestClient]:
    async def override_database_session() -> AsyncIterator[AsyncSession]:
        yield database_session

    async def override_dashboard_redis() -> AsyncIterator[AsyncRedis]:
        yield redis_client

    app.dependency_overrides[get_database_session] = override_database_session
    app.dependency_overrides[get_dashboard_redis] = override_dashboard_redis
    app.dependency_overrides[get_current_user] = lambda: current_user

    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.clear()


def create_summary() -> DashboardSummary:
    return DashboardSummary(
        total_monitors=12,
        operational_monitors=10,
        down_monitors=1,
        degraded_monitors=1,
        active_incidents=1,
        total_checks=1000,
        successful_checks=998,
        overall_uptime_percentage=99.8,
        average_response_time_ms=184.5,
    )


def test_get_dashboard_summary_returns_cached_metrics(
    client: TestClient,
    current_user: User,
) -> None:
    summary = create_summary()

    with patch(
        "app.api.v1.endpoints.dashboard.DashboardService.get_summary",
        new_callable=AsyncMock,
        return_value=summary,
    ) as get_summary:
        response = client.get("/api/v1/dashboard/summary")

    assert response.status_code == 200
    assert response.json() == summary.model_dump(
        mode="json",
    )
    get_summary.assert_awaited_once_with(
        current_user.id,
    )


def test_get_dashboard_summary_requires_authentication(
    database_session: AsyncMock,
    redis_client: MagicMock,
) -> None:
    async def override_database_session() -> AsyncIterator[AsyncSession]:
        yield database_session

    async def override_dashboard_redis() -> AsyncIterator[AsyncRedis]:
        yield redis_client

    app.dependency_overrides[get_database_session] = override_database_session
    app.dependency_overrides[get_dashboard_redis] = override_dashboard_redis

    try:
        with (
            patch(
                "app.api.v1.endpoints.dashboard.DashboardService.get_summary",
                new_callable=AsyncMock,
            ) as get_summary,
            TestClient(app) as test_client,
        ):
            response = test_client.get(
                "/api/v1/dashboard/summary",
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 401
    get_summary.assert_not_awaited()
