from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.monitor_check import MonitorCheck
from app.modules.checks.cursors import (
    CheckCursor,
    encode_check_cursor,
)


@dataclass(frozen=True, slots=True)
class MonitorCheckMetricsSummary:
    total_checks: int
    successful_checks: int
    average_response_time_ms: float | None


@dataclass(frozen=True, slots=True)
class MonitorCheckPage:
    items: list[MonitorCheck]
    next_cursor: str | None


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

    async def list_page_for_monitor(
        self,
        monitor_id: UUID,
        *,
        limit: int,
        cursor: CheckCursor | None = None,
    ) -> MonitorCheckPage:
        statement = select(MonitorCheck).where(MonitorCheck.monitor_id == monitor_id)

        if cursor is not None:
            statement = statement.where(
                or_(
                    MonitorCheck.checked_at < cursor.checked_at,
                    and_(
                        MonitorCheck.checked_at == cursor.checked_at,
                        MonitorCheck.id < cursor.check_id,
                    ),
                )
            )

        statement = statement.order_by(
            MonitorCheck.checked_at.desc(),
            MonitorCheck.id.desc(),
        ).limit(limit + 1)
        result = await self.session.execute(statement)
        checks = list(result.scalars().all())
        items = checks[:limit]
        next_cursor = None

        if len(checks) > limit and items:
            last_item = items[-1]
            next_cursor = encode_check_cursor(
                last_item.checked_at,
                last_item.id,
            )

        return MonitorCheckPage(
            items=items,
            next_cursor=next_cursor,
        )

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
