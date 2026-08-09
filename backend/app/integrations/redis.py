from redis import Redis
from redis.asyncio import Redis as AsyncRedis

from app.core.config import Settings, get_settings


def create_redis_client(settings: Settings | None = None) -> Redis:
    resolved_settings = settings or get_settings()

    return Redis.from_url(
        str(resolved_settings.redis_url),
        decode_responses=True,
        health_check_interval=30,
        socket_connect_timeout=5,
        socket_timeout=5,
    )


def create_async_redis_client(
    settings: Settings | None = None,
) -> AsyncRedis:
    resolved_settings = settings or get_settings()

    return AsyncRedis.from_url(
        str(resolved_settings.redis_url),
        decode_responses=True,
        health_check_interval=30,
        socket_connect_timeout=5,
        socket_timeout=5,
    )
