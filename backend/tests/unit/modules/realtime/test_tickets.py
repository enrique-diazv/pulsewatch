from hashlib import sha256
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from redis.asyncio import Redis as AsyncRedis

from app.modules.realtime.tickets import (
    RealtimeTicketService,
)


def create_redis_mock() -> MagicMock:
    redis_client = MagicMock(spec=AsyncRedis)
    redis_client.set = AsyncMock()
    redis_client.getdel = AsyncMock()

    return redis_client


@pytest.mark.anyio
async def test_issue_stores_hashed_single_use_ticket() -> None:
    redis_client = create_redis_mock()
    redis_client.set.return_value = True
    user_id = uuid4()
    raw_ticket = "single-use-ticket"
    ticket_hash = sha256(raw_ticket.encode("utf-8")).hexdigest()
    service = RealtimeTicketService(
        redis_client,
        ttl_seconds=30,
        ticket_factory=lambda: raw_ticket,
    )

    ticket = await service.issue(user_id)

    assert ticket == raw_ticket
    redis_client.set.assert_awaited_once_with(
        f"realtime-ticket:{ticket_hash}",
        str(user_id),
        ex=30,
        nx=True,
    )


@pytest.mark.anyio
async def test_issue_retries_ticket_collision() -> None:
    redis_client = create_redis_mock()
    redis_client.set.side_effect = [False, True]
    tickets = iter(("collision", "available"))
    service = RealtimeTicketService(
        redis_client,
        ttl_seconds=30,
        ticket_factory=lambda: next(tickets),
    )

    ticket = await service.issue(uuid4())

    assert ticket == "available"
    assert redis_client.set.await_count == 2


@pytest.mark.anyio
async def test_consume_uses_atomic_get_and_delete() -> None:
    redis_client = create_redis_mock()
    user_id = uuid4()
    redis_client.getdel.return_value = str(user_id)
    raw_ticket = "single-use-ticket"
    ticket_hash = sha256(raw_ticket.encode("utf-8")).hexdigest()
    service = RealtimeTicketService(
        redis_client,
        ttl_seconds=30,
    )

    consumed_user_id = await service.consume(raw_ticket)

    assert consumed_user_id == user_id
    redis_client.getdel.assert_awaited_once_with(f"realtime-ticket:{ticket_hash}")


@pytest.mark.anyio
async def test_consume_rejects_missing_ticket() -> None:
    redis_client = create_redis_mock()
    redis_client.getdel.return_value = None
    service = RealtimeTicketService(
        redis_client,
        ttl_seconds=30,
    )

    consumed_user_id = await service.consume("expired")

    assert consumed_user_id is None
