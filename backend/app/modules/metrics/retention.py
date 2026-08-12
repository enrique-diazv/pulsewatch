from datetime import UTC, datetime, timedelta

from sqlalchemy import delete, exists, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.database.models.incident import Incident
from app.database.models.monitor_check import MonitorCheck
from app.database.models.monitor_hourly_metric import (
    MonitorHourlyMetric,
)

MAX_RETENTION_BATCHES = 100


class MonitorCheckRetentionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def delete_aggregated_before(
        self,
        cutoff: datetime,
        *,
        limit: int,
    ) -> int:
        aggregate_exists = exists(
            select(
                MonitorHourlyMetric.monitor_id,
            ).where(
                MonitorHourlyMetric.monitor_id == MonitorCheck.monitor_id,
                MonitorHourlyMetric.hour
                == func.date_trunc(
                    "hour",
                    MonitorCheck.checked_at,
                    "UTC",
                ),
            )
        )
        incident_reference_exists = exists(
            select(Incident.id).where(
                or_(
                    Incident.initial_check_id == MonitorCheck.id,
                    Incident.recovery_check_id == MonitorCheck.id,
                )
            )
        )

        candidates = (
            select(MonitorCheck.id)
            .where(
                MonitorCheck.checked_at < cutoff,
                aggregate_exists,
                ~incident_reference_exists,
            )
            .order_by(
                MonitorCheck.checked_at.asc(),
                MonitorCheck.id.asc(),
            )
            .limit(limit)
            .cte("retention_candidates")
        )
        statement = delete(MonitorCheck).where(
            MonitorCheck.id.in_(
                select(candidates.c.id),
            )
        )
        result = await self.session.execute(statement)

        return result.rowcount or 0


class MonitorCheckRetentionService:
    def __init__(
        self,
        session: AsyncSession,
        settings: Settings | None = None,
        repository: MonitorCheckRetentionRepository | None = None,
    ) -> None:
        self.session = session
        self.settings = settings or get_settings()
        self.repository = repository or MonitorCheckRetentionRepository(session)

    async def purge(
        self,
        now: datetime | None = None,
    ) -> int:
        current_time = now or datetime.now(UTC)
        cutoff = current_time - timedelta(
            days=self.settings.raw_check_retention_days,
        )
        total_deleted = 0

        for _ in range(MAX_RETENTION_BATCHES):
            deleted = await self.repository.delete_aggregated_before(
                cutoff,
                limit=self.settings.retention_batch_size,
            )
            await self.session.commit()
            total_deleted += deleted

            if deleted < self.settings.retention_batch_size:
                break

        return total_deleted
