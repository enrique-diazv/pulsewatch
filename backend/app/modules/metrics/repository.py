from dataclasses import dataclass
from datetime import datetime, timedelta
from uuid import UUID

from sqlalchemy import DateTime, func, literal, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.monitor_check import MonitorCheck
from app.database.models.monitor_hourly_metric import (
    MonitorHourlyMetric,
)


@dataclass(frozen=True, slots=True)
class HourlyMetricSummary:
    total_checks: int
    successful_checks: int
    average_response_time_ms: float | None


class HourlyMetricRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def upsert_hour(
        self,
        hour: datetime,
    ) -> int:
        next_hour = hour + timedelta(hours=1)
        total_checks = func.count(MonitorCheck.id)
        successful_checks = func.count(
            MonitorCheck.id,
        ).filter(MonitorCheck.success.is_(True))
        failed_checks = func.count(
            MonitorCheck.id,
        ).filter(MonitorCheck.success.is_(False))

        aggregation = (
            select(
                MonitorCheck.monitor_id,
                literal(
                    hour,
                    type_=DateTime(timezone=True),
                ).label("hour"),
                total_checks.label("total_checks"),
                successful_checks.label(
                    "successful_checks",
                ),
                failed_checks.label("failed_checks"),
                func.avg(
                    MonitorCheck.response_time_ms,
                ).label("average_response_time_ms"),
                func.min(
                    MonitorCheck.response_time_ms,
                ).label("min_response_time_ms"),
                func.max(
                    MonitorCheck.response_time_ms,
                ).label("max_response_time_ms"),
                (successful_checks * 100.0 / total_checks).label("uptime_percentage"),
                func.now().label("updated_at"),
            )
            .where(
                MonitorCheck.checked_at >= hour,
                MonitorCheck.checked_at < next_hour,
            )
            .group_by(MonitorCheck.monitor_id)
        )

        insert_statement = insert(
            MonitorHourlyMetric,
        ).from_select(
            [
                "monitor_id",
                "hour",
                "total_checks",
                "successful_checks",
                "failed_checks",
                "average_response_time_ms",
                "min_response_time_ms",
                "max_response_time_ms",
                "uptime_percentage",
                "updated_at",
            ],
            aggregation,
        )

        statement = insert_statement.on_conflict_do_update(
            index_elements=[
                MonitorHourlyMetric.monitor_id,
                MonitorHourlyMetric.hour,
            ],
            set_={
                "total_checks": (insert_statement.excluded.total_checks),
                "successful_checks": (insert_statement.excluded.successful_checks),
                "failed_checks": (insert_statement.excluded.failed_checks),
                "average_response_time_ms": (
                    insert_statement.excluded.average_response_time_ms
                ),
                "min_response_time_ms": (
                    insert_statement.excluded.min_response_time_ms
                ),
                "max_response_time_ms": (
                    insert_statement.excluded.max_response_time_ms
                ),
                "uptime_percentage": (insert_statement.excluded.uptime_percentage),
                "updated_at": func.now(),
            },
        )

        result = await self.session.execute(statement)

        return result.rowcount or 0

    async def summarize_for_monitor(
        self,
        monitor_id: UUID,
        *,
        from_hour: datetime,
        to_hour: datetime,
    ) -> HourlyMetricSummary:
        weighted_response_time = func.sum(
            MonitorHourlyMetric.average_response_time_ms
            * MonitorHourlyMetric.total_checks,
        )
        total_checks = func.sum(
            MonitorHourlyMetric.total_checks,
        )

        statement = select(
            func.coalesce(total_checks, 0).label(
                "total_checks",
            ),
            func.coalesce(
                func.sum(
                    MonitorHourlyMetric.successful_checks,
                ),
                0,
            ).label("successful_checks"),
            (weighted_response_time / func.nullif(total_checks, 0)).label(
                "average_response_time_ms"
            ),
        ).where(
            MonitorHourlyMetric.monitor_id == monitor_id,
            MonitorHourlyMetric.hour >= from_hour,
            MonitorHourlyMetric.hour < to_hour,
        )
        result = await self.session.execute(statement)
        row = result.one()
        average_response_time = row.average_response_time_ms

        return HourlyMetricSummary(
            total_checks=int(row.total_checks),
            successful_checks=int(
                row.successful_checks,
            ),
            average_response_time_ms=(
                float(average_response_time)
                if average_response_time is not None
                else None
            ),
        )
