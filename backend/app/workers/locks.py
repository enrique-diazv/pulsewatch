from collections.abc import Iterator
from contextlib import contextmanager
from uuid import UUID

from redis import Redis
from redis.exceptions import LockNotOwnedError

from app.core.logging import get_logger

DEFAULT_MONITOR_LOCK_TTL_SECONDS = 120

logger = get_logger(__name__)


@contextmanager
def acquire_monitor_lock(
    redis_client: Redis,
    monitor_id: UUID,
    *,
    ttl_seconds: int = DEFAULT_MONITOR_LOCK_TTL_SECONDS,
) -> Iterator[bool]:
    lock = redis_client.lock(
        f"monitor-lock:{monitor_id}",
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
                    "monitor_lock_release_skipped",
                    extra={"monitor_id": str(monitor_id)},
                )
