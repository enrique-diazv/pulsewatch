import asyncio
from collections.abc import AsyncIterator
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import WebSocket

from app.modules.realtime.connections import stream_user_events


class FakeSubscription:
    def __init__(self, payload: str) -> None:
        self.payload = payload
        self.subscribe = AsyncMock()
        self.unsubscribe = AsyncMock()
        self.aclose = AsyncMock()

    async def listen(self) -> AsyncIterator[dict[str, object]]:
        yield {
            "type": "subscribe",
            "data": 1,
        }
        yield {
            "type": "message",
            "data": self.payload,
        }

        await asyncio.Event().wait()


@pytest.mark.anyio
async def test_stream_user_events_forwards_messages_and_cleans_up() -> None:
    payload = '{"type":"monitor.updated"}'
    channel = "realtime:user:test-user"
    message_forwarded = asyncio.Event()
    websocket = MagicMock(spec=WebSocket)
    subscription = FakeSubscription(payload)

    websocket.accept = AsyncMock()

    async def send_text(message: str) -> None:
        assert message == payload
        message_forwarded.set()

    async def receive() -> dict[str, str]:
        await message_forwarded.wait()

        return {"type": "websocket.disconnect"}

    websocket.send_text = AsyncMock(side_effect=send_text)
    websocket.receive = AsyncMock(side_effect=receive)

    await stream_user_events(
        websocket,
        subscription,
        channel,
    )

    subscription.subscribe.assert_awaited_once_with(channel)
    websocket.accept.assert_awaited_once()
    websocket.send_text.assert_awaited_once_with(payload)
    subscription.unsubscribe.assert_awaited_once_with(channel)
    subscription.aclose.assert_awaited_once()
