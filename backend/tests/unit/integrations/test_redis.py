from unittest.mock import patch

from app.core.config import Settings
from app.integrations.redis import create_async_redis_client, create_redis_client


def test_create_redis_client_uses_application_settings() -> None:
    settings = Settings(
        _env_file=None,
        database_password="test-password",
        jwt_secret_key="test-jwt-secret-key-with-at-least-32-characters",
        redis_url="redis://127.0.0.1:6379/4",
    )

    with patch("app.integrations.redis.Redis.from_url") as from_url:
        client = create_redis_client(settings)

    assert client is from_url.return_value
    from_url.assert_called_once_with(
        "redis://127.0.0.1:6379/4",
        decode_responses=True,
        health_check_interval=30,
        socket_connect_timeout=5,
        socket_timeout=5,
    )


def test_create_async_redis_client_uses_application_settings() -> None:
    settings = Settings(
        _env_file=None,
        database_password="test-password",
        jwt_secret_key="test-jwt-secret-key-with-at-least-32-characters",
        redis_url="redis://127.0.0.1:6379/5",
    )

    with patch(
        "app.integrations.redis.AsyncRedis.from_url",
    ) as from_url:
        client = create_async_redis_client(settings)

    assert client is from_url.return_value
    from_url.assert_called_once_with(
        "redis://127.0.0.1:6379/5",
        decode_responses=True,
        health_check_interval=30,
        socket_connect_timeout=5,
        socket_timeout=5,
    )
