from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from redis.asyncio import Redis as AsyncRedis
from redis.exceptions import RedisError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.modules.dashboard.repository import (
    DashboardRepository,
    DashboardSummaryData,
)
from app.modules.dashboard.schemas import DashboardSummary
from app.modules.dashboard.service import (
    DashboardService,
    build_dashboard_cache_key,
    invalidate_dashboard_cache,
)


def create_redis_mock() -> MagicMock:
    redis_client = MagicMock(spec=AsyncRedis)
    redis_client.get = AsyncMock()
    redis_client.set = AsyncMock()
    redis_client.delete = AsyncMock()
    return redis_client


def create_settings() -> Settings:
    return Settings(
        database_password="test-password",
        jwt_secret_key=("test-jwt-secret-key-with-at-least-32-characters"),
        dashboard_cache_ttl_seconds=30,
        _env_file=None,
    )


def create_summary_data() -> DashboardSummaryData:
    return DashboardSummaryData(
        total_monitors=12,
        operational_monitors=10,
        down_monitors=1,
        degraded_monitors=1,
        active_incidents=1,
        total_checks=1000,
        successful_checks=998,
        average_response_time_ms=184.5,
    )


@pytest.mark.anyio
async def test_get_summary_returns_cached_payload() -> None:
    session = AsyncMock(spec=AsyncSession)
    redis_client = create_redis_mock()
    repository = AsyncMock(spec=DashboardRepository)
    cached_summary = DashboardSummary(
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
    redis_client.get.return_value = cached_summary.model_dump_json()
    user_id = uuid4()
    service = DashboardService(
        session,
        redis_client,
        create_settings(),
        repository,
    )

    summary = await service.get_summary(user_id)

    assert summary == cached_summary
    redis_client.get.assert_awaited_once_with(
        build_dashboard_cache_key(user_id),
    )
    repository.summarize_for_user.assert_not_awaited()
    redis_client.set.assert_not_awaited()


@pytest.mark.anyio
async def test_get_summary_caches_database_result() -> None:
    session = AsyncMock(spec=AsyncSession)
    redis_client = create_redis_mock()
    redis_client.get.return_value = None
    repository = AsyncMock(spec=DashboardRepository)
    repository.summarize_for_user.return_value = create_summary_data()
    user_id = uuid4()
    service = DashboardService(
        session,
        redis_client,
        create_settings(),
        repository,
    )

    summary = await service.get_summary(user_id)

    assert summary.overall_uptime_percentage == 99.8
    repository.summarize_for_user.assert_awaited_once_with(
        user_id,
    )
    redis_client.set.assert_awaited_once_with(
        build_dashboard_cache_key(user_id),
        summary.model_dump_json(),
        ex=30,
    )


@pytest.mark.anyio
async def test_get_summary_falls_back_when_redis_fails() -> None:
    session = AsyncMock(spec=AsyncSession)
    redis_client = create_redis_mock()
    redis_client.get.side_effect = RedisError(
        "Redis unavailable",
    )
    redis_client.set.side_effect = RedisError(
        "Redis unavailable",
    )
    repository = AsyncMock(spec=DashboardRepository)
    repository.summarize_for_user.return_value = create_summary_data()
    user_id = uuid4()
    service = DashboardService(
        session,
        redis_client,
        create_settings(),
        repository,
    )

    summary = await service.get_summary(user_id)

    assert summary.total_monitors == 12
    assert summary.overall_uptime_percentage == 99.8
    repository.summarize_for_user.assert_awaited_once_with(
        user_id,
    )


@pytest.mark.anyio
async def test_invalidate_dashboard_cache_deletes_user_key() -> None:
    redis_client = create_redis_mock()
    user_id = uuid4()

    await invalidate_dashboard_cache(
        redis_client,
        user_id,
    )

    redis_client.delete.assert_awaited_once_with(
        build_dashboard_cache_key(user_id),
    )


@pytest.mark.anyio
async def test_invalidate_dashboard_cache_ignores_redis_failure() -> None:
    redis_client = create_redis_mock()
    redis_client.delete.side_effect = RedisError(
        "Redis unavailable",
    )

    await invalidate_dashboard_cache(
        redis_client,
        uuid4(),
    )
