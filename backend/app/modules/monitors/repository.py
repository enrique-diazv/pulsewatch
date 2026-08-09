from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.monitor import Monitor


class MonitorRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def delete(self, monitor: Monitor) -> None:
        await self.session.delete(monitor)

    async def add(self, monitor: Monitor) -> Monitor:
        self.session.add(monitor)
        await self.session.flush()

        return monitor

    async def list_for_user(self, user_id: UUID) -> list[Monitor]:
        statement = (
            select(Monitor)
            .where(Monitor.user_id == user_id)
            .order_by(
                Monitor.created_at.desc(),
                Monitor.id.desc(),
            )
        )
        result = await self.session.execute(statement)

        return list(result.scalars().all())

    async def get_by_id(self, monitor_id: UUID) -> Monitor | None:
        statement = select(Monitor).where(Monitor.id == monitor_id)
        result = await self.session.execute(statement)

        return result.scalar_one_or_none()

    async def get_for_user(
        self,
        monitor_id: UUID,
        user_id: UUID,
    ) -> Monitor | None:
        statement = select(Monitor).where(
            Monitor.id == monitor_id,
            Monitor.user_id == user_id,
        )
        result = await self.session.execute(statement)

        return result.scalar_one_or_none()
