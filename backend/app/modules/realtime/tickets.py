from collections.abc import Callable
from hashlib import sha256
from secrets import token_urlsafe
from uuid import UUID

from redis.asyncio import Redis as AsyncRedis


def create_ticket() -> str:
    return token_urlsafe(32)


def build_ticket_key(ticket: str) -> str:
    ticket_hash = sha256(ticket.encode("utf-8")).hexdigest()

    return f"realtime-ticket:{ticket_hash}"


class RealtimeTicketService:
    def __init__(
        self,
        redis_client: AsyncRedis,
        *,
        ttl_seconds: int,
        ticket_factory: Callable[[], str] = create_ticket,
    ) -> None:
        self.redis_client = redis_client
        self.ttl_seconds = ttl_seconds
        self.ticket_factory = ticket_factory

    async def issue(self, user_id: UUID) -> str:
        for _ in range(3):
            ticket = self.ticket_factory()
            stored = await self.redis_client.set(
                build_ticket_key(ticket),
                str(user_id),
                ex=self.ttl_seconds,
                nx=True,
            )

            if stored:
                return ticket

        raise RuntimeError("Unable to allocate realtime ticket")

    async def consume(self, ticket: str) -> UUID | None:
        stored_user_id = await self.redis_client.getdel(build_ticket_key(ticket))

        if stored_user_id is None:
            return None

        try:
            return UUID(stored_user_id)
        except (TypeError, ValueError):
            return None
