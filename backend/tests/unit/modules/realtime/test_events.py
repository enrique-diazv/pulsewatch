from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from redis.asyncio import Redis as AsyncRedis

from app.modules.monitors.enums import MonitorStatus
from app.modules.realtime.events import (
    RealtimeEvent,
    RealtimeEventType,
    RedisRealtimePublisher,
    build_user_channel,
)


def create_redis_mock() -> MagicMock:
    redis_client = MagicMock(spec=AsyncRedis)
    redis_client.publish = AsyncMock()

    return redis_client


def test_user_channel_is_scoped_by_user_id() -> None:
    user_id = uuid4()

    assert build_user_channel(user_id) == (f"realtime:user:{user_id}")


def test_realtime_event_serializes_stable_contract() -> None:
    monitor_id = uuid4()
    event = RealtimeEvent(
        type=RealtimeEventType.MONITOR_UPDATED,
        occurred_at=datetime(
            2026,
            8,
            9,
            22,
            0,
            tzinfo=UTC,
        ),
        monitor_id=monitor_id,
        monitor_status=MonitorStatus.DOWN,
        check_id=42,
    )

    payload = event.model_dump(mode="json")

    assert payload["type"] == "monitor.updated"
    assert payload["monitor_id"] == str(monitor_id)
    assert payload["monitor_status"] == "DOWN"
    assert payload["check_id"] == 42
    assert payload["incident_id"] is None


@pytest.mark.anyio
async def test_redis_publisher_uses_private_channel() -> None:
    redis_client = create_redis_mock()
    publisher = RedisRealtimePublisher(redis_client)
    user_id = uuid4()
    event = RealtimeEvent(
        type=RealtimeEventType.INCIDENT_OPENED,
        monitor_id=uuid4(),
        monitor_status=MonitorStatus.DOWN,
        check_id=42,
        incident_id=uuid4(),
    )

    await publisher.publish(user_id, event)

    redis_client.publish.assert_awaited_once_with(
        f"realtime:user:{user_id}",
        event.model_dump_json(),
    )
