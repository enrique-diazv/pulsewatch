from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.monitor_check import MonitorCheck


@dataclass(frozen=True, slots=True)
class MonitorCheckMetricsSummary:
    total_checks: int
    successful_checks: int
    average_response_time_ms: float | None


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

    async def summarize_for_monitor(
        self,
        monitor_id: UUID,
        *,
        from_timestamp: datetime,
        to_timestamp: datetime,
    ) -> MonitorCheckMetricsSummary:
        statement = select(
            func.count(MonitorCheck.id).label("total_checks"),
            func.count(MonitorCheck.id)
            .filter(MonitorCheck.success.is_(True))
            .label("successful_checks"),
            func.avg(MonitorCheck.response_time_ms).label("average_response_time_ms"),
        ).where(
            MonitorCheck.monitor_id == monitor_id,
            MonitorCheck.checked_at >= from_timestamp,
            MonitorCheck.checked_at <= to_timestamp,
        )
        result = await self.session.execute(statement)
        row = result.one()
        average_response_time = row.average_response_time_ms

        return MonitorCheckMetricsSummary(
            total_checks=int(row.total_checks),
            successful_checks=int(row.successful_checks),
            average_response_time_ms=(
                float(average_response_time)
                if average_response_time is not None
                else None
            ),
        )
