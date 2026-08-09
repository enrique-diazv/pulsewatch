from unittest.mock import MagicMock, patch
from uuid import uuid4

from redis import Redis
from redis.exceptions import LockNotOwnedError

from app.workers.locks import acquire_monitor_lock


def test_acquire_monitor_lock_releases_owned_lock() -> None:
    redis_client = MagicMock(spec=Redis)
    lock = MagicMock()
    lock.acquire.return_value = True
    redis_client.lock.return_value = lock
    monitor_id = uuid4()

    with acquire_monitor_lock(redis_client, monitor_id) as acquired:
        assert acquired is True

    redis_client.lock.assert_called_once_with(
        f"monitor-lock:{monitor_id}",
        timeout=120,
        blocking=False,
    )
    lock.acquire.assert_called_once_with(blocking=False)
    lock.release.assert_called_once()


def test_acquire_monitor_lock_skips_busy_monitor() -> None:
    redis_client = MagicMock(spec=Redis)
    lock = MagicMock()
    lock.acquire.return_value = False
    redis_client.lock.return_value = lock

    with acquire_monitor_lock(redis_client, uuid4()) as acquired:
        assert acquired is False

    lock.release.assert_not_called()


def test_acquire_monitor_lock_handles_expired_ownership() -> None:
    redis_client = MagicMock(spec=Redis)
    lock = MagicMock()
    lock.acquire.return_value = True
    lock.release.side_effect = LockNotOwnedError("Lock is no longer owned")
    redis_client.lock.return_value = lock
    monitor_id = uuid4()

    with (
        patch("app.workers.locks.logger.warning") as warning,
        acquire_monitor_lock(redis_client, monitor_id) as acquired,
    ):
        assert acquired is True

    warning.assert_called_once_with(
        "monitor_lock_release_skipped",
        extra={"monitor_id": str(monitor_id)},
    )
