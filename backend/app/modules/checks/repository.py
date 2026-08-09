from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.monitor_check import MonitorCheck


class MonitorCheckRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add(self, monitor_check: MonitorCheck) -> MonitorCheck:
        self.session.add(monitor_check)
        await self.session.flush()

        return monitor_check

    async def list_for_monitor(
        self,
        monitor_id: UUID,
        *,
        limit: int,
    ) -> list[MonitorCheck]:
        statement = (
            select(MonitorCheck)
            .where(MonitorCheck.monitor_id == monitor_id)
            .order_by(
                MonitorCheck.checked_at.desc(),
                MonitorCheck.id.desc(),
            )
            .limit(limit)
        )
        result = await self.session.execute(statement)

        return list(result.scalars().all())
