from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.monitor_check import MonitorCheck


class MonitorCheckRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add(self, monitor_check: MonitorCheck) -> MonitorCheck:
        self.session.add(monitor_check)
        await self.session.flush()

        return monitor_check
