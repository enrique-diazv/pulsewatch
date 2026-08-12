from datetime import UTC, datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.metrics.repository import (
    HourlyMetricRepository,
)


def normalize_metric_hour(value: datetime) -> datetime:
    if value.tzinfo is None:
        raise ValueError(
            "Metric aggregation hour must be timezone-aware",
        )

    return value.astimezone(UTC).replace(
        minute=0,
        second=0,
        microsecond=0,
    )


class HourlyMetricAggregationService:
    def __init__(
        self,
        session: AsyncSession,
        repository: HourlyMetricRepository | None = None,
    ) -> None:
        self.session = session
        self.repository = repository or HourlyMetricRepository(
            session,
        )

    async def aggregate_hour(
        self,
        hour: datetime,
    ) -> int:
        normalized_hour = normalize_metric_hour(hour)
        affected_rows = await self.repository.upsert_hour(
            normalized_hour,
        )
        await self.session.commit()

        return affected_rows

    async def aggregate_previous_hour(
        self,
        now: datetime | None = None,
    ) -> int:
        current_hour = normalize_metric_hour(
            now or datetime.now(UTC),
        )
        previous_hour = current_hour - timedelta(hours=1)

        return await self.aggregate_hour(previous_hour)
