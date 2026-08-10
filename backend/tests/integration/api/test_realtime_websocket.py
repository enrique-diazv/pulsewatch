import asyncio
from collections.abc import AsyncIterator
from hashlib import sha256
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from redis.asyncio import Redis as AsyncRedis
from starlette.websockets import WebSocketDisconnect

from app.main import app


class FakeSubscription:
    def __init__(self, payload: str) -> None:
        self.payload = payload
        self.subscribe = AsyncMock()
        self.unsubscribe = AsyncMock()
        self.aclose = AsyncMock()

    async def listen(self) -> AsyncIterator[dict[str, object]]:
        yield {
            "type": "message",
            "data": self.payload,
        }

        await asyncio.Event().wait()


def create_redis_mock(
    stored_user_id: str | None,
    subscription: FakeSubscription,
) -> MagicMock:
    redis_client = MagicMock(spec=AsyncRedis)
    redis_client.getdel = AsyncMock(return_value=stored_user_id)
    redis_client.pubsub.return_value = subscription
    redis_client.aclose = AsyncMock()

    return redis_client


def test_websocket_consumes_ticket_and_forwards_event() -> None:
    user_id = uuid4()
    ticket = f"realtime-ticket-{'x' * 32}"
    payload = '{"type":"monitor.updated"}'
    subscription = FakeSubscription(payload)
    redis_client = create_redis_mock(
        str(user_id),
        subscription,
    )

    with (
        patch(
            "app.api.v1.endpoints.realtime.create_async_redis_client",
            return_value=redis_client,
        ),
        TestClient(app) as client,
        client.websocket_connect(f"/api/v1/realtime/ws?ticket={ticket}") as websocket,
    ):
        assert websocket.receive_text() == payload

    ticket_hash = sha256(ticket.encode("utf-8")).hexdigest()
    redis_client.getdel.assert_awaited_once_with(f"realtime-ticket:{ticket_hash}")
    subscription.subscribe.assert_awaited_once_with(f"realtime:user:{user_id}")
    subscription.unsubscribe.assert_awaited_once()
    subscription.aclose.assert_awaited_once()
    redis_client.aclose.assert_awaited_once()


def test_websocket_rejects_invalid_ticket() -> None:
    ticket = f"invalid-ticket-{'x' * 32}"
    subscription = FakeSubscription("{}")
    redis_client = create_redis_mock(
        None,
        subscription,
    )

    with (
        patch(
            "app.api.v1.endpoints.realtime.create_async_redis_client",
            return_value=redis_client,
        ),
        TestClient(app) as client,
        pytest.raises(WebSocketDisconnect) as captured,
        client.websocket_connect(f"/api/v1/realtime/ws?ticket={ticket}"),
    ):
        pass

    assert captured.value.code == status.WS_1008_POLICY_VIOLATION
    redis_client.pubsub.assert_not_called()
    redis_client.aclose.assert_awaited_once()
