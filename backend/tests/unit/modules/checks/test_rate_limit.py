from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
from redis.asyncio import Redis as AsyncRedis

from app.core.config import Settings
from app.modules.checks.rate_limit import reserve_manual_check_slot


def create_settings() -> Settings:
    return Settings(
        _env_file=None,
        database_password="test-password",
        jwt_secret_key="test-jwt-secret-key-with-at-least-32-characters",
        redis_url="redis://127.0.0.1:6379/0",
        manual_check_cooldown_seconds=10,
    )


@pytest.mark.anyio
async def test_reserve_manual_check_slot_sets_atomic_cooldown() -> None:
    redis_client = AsyncMock(spec=AsyncRedis)
    redis_client.set = AsyncMock(return_value=True)
    redis_client.aclose = AsyncMock()
    user_id = uuid4()
    monitor_id = uuid4()

    with patch(
        "app.modules.checks.rate_limit.create_async_redis_client",
        return_value=redis_client,
    ):
        reserved = await reserve_manual_check_slot(
            user_id,
            monitor_id,
            settings=create_settings(),
        )

    assert reserved is True
    redis_client.set.assert_awaited_once_with(
        f"manual-check-rate-limit:{user_id}:{monitor_id}",
        "1",
        ex=10,
        nx=True,
    )
    redis_client.aclose.assert_awaited_once()


@pytest.mark.anyio
async def test_reserve_manual_check_slot_rejects_existing_cooldown() -> None:
    redis_client = AsyncMock(spec=AsyncRedis)
    redis_client.set = AsyncMock(return_value=None)
    redis_client.aclose = AsyncMock()

    with patch(
        "app.modules.checks.rate_limit.create_async_redis_client",
        return_value=redis_client,
    ):
        reserved = await reserve_manual_check_slot(
            uuid4(),
            uuid4(),
            settings=create_settings(),
        )

    assert reserved is False
    redis_client.aclose.assert_awaited_once()
