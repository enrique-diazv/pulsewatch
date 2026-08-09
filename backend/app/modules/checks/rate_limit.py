from uuid import UUID

from app.core.config import Settings, get_settings
from app.integrations.redis import create_async_redis_client


async def reserve_manual_check_slot(
    user_id: UUID,
    monitor_id: UUID,
    *,
    settings: Settings | None = None,
) -> bool:
    resolved_settings = settings or get_settings()
    redis_client = create_async_redis_client(resolved_settings)
    key = f"manual-check-rate-limit:{user_id}:{monitor_id}"

    try:
        reserved = await redis_client.set(
            key,
            "1",
            ex=resolved_settings.manual_check_cooldown_seconds,
            nx=True,
        )
    finally:
        await redis_client.aclose()

    return bool(reserved)
