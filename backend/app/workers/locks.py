from collections.abc import Iterator
from contextlib import contextmanager
from uuid import UUID

from redis import Redis
from redis.exceptions import LockNotOwnedError

from app.core.logging import get_logger

DEFAULT_MONITOR_LOCK_TTL_SECONDS = 120
DEFAULT_NOTIFICATION_LOCK_TTL_SECONDS = 60

logger = get_logger(__name__)


@contextmanager
def acquire_distributed_lock(
    redis_client: Redis,
    *,
    key: str,
    ttl_seconds: int,
    release_warning_event: str,
    resource_id: UUID,
) -> Iterator[bool]:
    lock = redis_client.lock(
        key,
        timeout=ttl_seconds,
        blocking=False,
    )
    acquired = bool(lock.acquire(blocking=False))

    try:
        yield acquired
    finally:
        if acquired:
            try:
                lock.release()
            except LockNotOwnedError:
                logger.warning(
                    release_warning_event,
                    extra={
                        "resource_id": str(resource_id),
                    },
                )


@contextmanager
def acquire_monitor_lock(
    redis_client: Redis,
    monitor_id: UUID,
    *,
    ttl_seconds: int = DEFAULT_MONITOR_LOCK_TTL_SECONDS,
) -> Iterator[bool]:
    with acquire_distributed_lock(
        redis_client,
        key=f"monitor-lock:{monitor_id}",
        ttl_seconds=ttl_seconds,
        release_warning_event=("monitor_lock_release_skipped"),
        resource_id=monitor_id,
    ) as acquired:
        yield acquired


@contextmanager
def acquire_notification_lock(
    redis_client: Redis,
    notification_id: UUID,
    *,
    ttl_seconds: int = (DEFAULT_NOTIFICATION_LOCK_TTL_SECONDS),
) -> Iterator[bool]:
    with acquire_distributed_lock(
        redis_client,
        key=f"notification-lock:{notification_id}",
        ttl_seconds=ttl_seconds,
        release_warning_event=("notification_lock_release_skipped"),
        resource_id=notification_id,
    ) as acquired:
        yield acquired
