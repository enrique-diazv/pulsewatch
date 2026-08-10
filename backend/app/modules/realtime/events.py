from datetime import UTC, datetime
from enum import StrEnum
from typing import Protocol
from uuid import UUID, uuid4

from pydantic import BaseModel, Field
from redis.asyncio import Redis as AsyncRedis

from app.modules.monitors.enums import MonitorStatus


class RealtimeEventType(StrEnum):
    MONITOR_UPDATED = "monitor.updated"
    INCIDENT_OPENED = "incident.opened"
    INCIDENT_RESOLVED = "incident.resolved"


class RealtimeEvent(BaseModel):
    event_id: UUID = Field(default_factory=uuid4)
    type: RealtimeEventType
    occurred_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    monitor_id: UUID
    monitor_status: MonitorStatus
    check_id: int
    incident_id: UUID | None = None


def build_user_channel(user_id: UUID) -> str:
    return f"realtime:user:{user_id}"


class RealtimePublisher(Protocol):
    async def publish(
        self,
        user_id: UUID,
        event: RealtimeEvent,
    ) -> None: ...


class RedisRealtimePublisher:
    def __init__(self, redis_client: AsyncRedis) -> None:
        self.redis_client = redis_client

    async def publish(
        self,
        user_id: UUID,
        event: RealtimeEvent,
    ) -> None:
        await self.redis_client.publish(
            build_user_channel(user_id),
            event.model_dump_json(),
        )
