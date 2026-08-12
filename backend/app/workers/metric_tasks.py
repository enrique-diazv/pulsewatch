from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.logging import get_logger
from app.database.session import async_session_factory
from app.modules.metrics.retention import (
    MonitorCheckRetentionService,
)
from app.modules.metrics.service import (
    HourlyMetricAggregationService,
)
from app.workers.celery_app import celery_app
from app.workers.monitor_tasks import run_worker_coroutine

logger = get_logger(__name__)


async def aggregate_closed_hour(
    session: AsyncSession,
    now: datetime | None = None,
) -> int:
    return await HourlyMetricAggregationService(
        session,
    ).aggregate_previous_hour(now)


async def _aggregate_hourly_metrics_task() -> None:
    async with async_session_factory() as session:
        affected_rows = await aggregate_closed_hour(
            session,
        )

    logger.info(
        "hourly_metric_aggregation_completed",
        extra={"affected_rows": affected_rows},
    )


async def _purge_expired_monitor_checks_task() -> None:
    settings = get_settings()

    async with async_session_factory() as session:
        deleted_checks = await MonitorCheckRetentionService(
            session,
            settings,
        ).purge()

    logger.info(
        "monitor_check_retention_completed",
        extra={"deleted_checks": deleted_checks},
    )


@celery_app.task(
    name=("app.workers.metric_tasks.aggregate_hourly_metrics"),
)
def aggregate_hourly_metrics() -> None:
    run_worker_coroutine(
        _aggregate_hourly_metrics_task(),
    )


@celery_app.task(
    name=("app.workers.metric_tasks.purge_expired_monitor_checks"),
)
def purge_expired_monitor_checks() -> None:
    run_worker_coroutine(
        _purge_expired_monitor_checks_task(),
    )
