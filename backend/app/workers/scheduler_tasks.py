from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.logging import get_logger
from app.database.session import async_session_factory
from app.modules.checks.queue import enqueue_monitor_check
from app.modules.monitors.scheduling import MonitorSchedulingService
from app.workers.celery_app import celery_app
from app.workers.monitor_tasks import run_worker_coroutine

logger = get_logger(__name__)


async def enqueue_due_monitors(
    session: AsyncSession,
    *,
    batch_size: int,
) -> int:
    service = MonitorSchedulingService(session)
    monitor_ids = await service.claim_due_monitors(
        limit=batch_size,
    )
    queued_count = 0

    for monitor_id in monitor_ids:
        try:
            enqueue_monitor_check(monitor_id)
        except Exception:
            logger.exception(
                "monitor_schedule_enqueue_failed",
                extra={"monitor_id": str(monitor_id)},
            )
        else:
            queued_count += 1

    return queued_count


async def _schedule_due_monitors_task() -> None:
    settings = get_settings()

    async with async_session_factory() as session:
        queued_count = await enqueue_due_monitors(
            session,
            batch_size=settings.scheduler_batch_size,
        )

    logger.info(
        "monitor_scheduling_completed",
        extra={"queued_count": queued_count},
    )


@celery_app.task(
    name="app.workers.scheduler_tasks.schedule_due_monitors",
)
def schedule_due_monitors() -> None:
    run_worker_coroutine(_schedule_due_monitors_task())
