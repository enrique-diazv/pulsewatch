from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.monitors.repository import MonitorRepository


class MonitorSchedulingService:
    def __init__(
        self,
        session: AsyncSession,
        repository: MonitorRepository | None = None,
    ) -> None:
        self.session = session
        self.repository = repository or MonitorRepository(session)

    async def claim_due_monitors(
        self,
        *,
        limit: int,
        now: datetime | None = None,
    ) -> list[UUID]:
        claimed_at = now or datetime.now(UTC)
        monitors = await self.repository.list_due_for_update(
            claimed_at,
            limit=limit,
        )

        for monitor in monitors:
            monitor.next_check_at = claimed_at + timedelta(
                seconds=monitor.interval_seconds,
            )

        await self.session.commit()

        return [monitor.id for monitor in monitors]
