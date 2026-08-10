import asyncio
from typing import Any

from fastapi import WebSocket, WebSocketDisconnect
from redis.asyncio.client import PubSub


async def _forward_messages(
    websocket: WebSocket,
    subscription: PubSub,
) -> None:
    async for message in subscription.listen():
        if message.get("type") != "message":
            continue

        data = message.get("data")

        if isinstance(data, bytes):
            payload = data.decode("utf-8")
        elif isinstance(data, str):
            payload = data
        else:
            continue

        await websocket.send_text(payload)


async def _wait_for_disconnect(websocket: WebSocket) -> None:
    while True:
        message = await websocket.receive()

        if message["type"] == "websocket.disconnect":
            return


async def stream_user_events(
    websocket: WebSocket,
    subscription: PubSub,
    channel: str,
) -> None:
    await subscription.subscribe(channel)
    await websocket.accept()

    sender = asyncio.create_task(_forward_messages(websocket, subscription))
    receiver = asyncio.create_task(_wait_for_disconnect(websocket))

    try:
        done, pending = await asyncio.wait(
            {sender, receiver},
            return_when=asyncio.FIRST_COMPLETED,
        )

        for task in pending:
            task.cancel()

        results: list[Any] = await asyncio.gather(
            *done,
            *pending,
            return_exceptions=True,
        )

        for result in results:
            if isinstance(result, Exception) and not isinstance(
                result,
                WebSocketDisconnect,
            ):
                raise result
    finally:
        await subscription.unsubscribe(channel)
        await subscription.aclose()
