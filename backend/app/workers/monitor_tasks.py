import asyncio
import selectors
import sys
from collections.abc import Coroutine
from typing import Any
from uuid import UUID

import httpx2
from redis.asyncio import Redis as AsyncRedis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.database.models.monitor_check import MonitorCheck
from app.database.session import async_session_factory
from app.integrations.redis import create_async_redis_client, create_redis_client
from app.modules.checks.engine import HttpCheckEngine
from app.modules.checks.service import CheckExecutionService
from app.modules.dashboard.service import (
    invalidate_dashboard_cache,
)
from app.modules.monitors.repository import MonitorRepository
from app.modules.realtime.events import (
    RealtimePublisher,
    RedisRealtimePublisher,
)
from app.workers.celery_app import celery_app
from app.workers.locks import acquire_monitor_lock

logger = get_logger(__name__)


def create_selector_event_loop() -> asyncio.AbstractEventLoop:
    return asyncio.SelectorEventLoop(selectors.SelectSelector())


def run_worker_coroutine(
    coroutine: Coroutine[Any, Any, None],
) -> None:
    if sys.platform == "win32":
        asyncio.run(
            coroutine,
            loop_factory=create_selector_event_loop,
        )
        return

    asyncio.run(coroutine)


async def execute_monitor_check(
    monitor_id: UUID,
    session: AsyncSession,
    client: httpx2.AsyncClient,
    realtime_publisher: RealtimePublisher | None = None,
    dashboard_redis: AsyncRedis | None = None,
) -> MonitorCheck | None:
    repository = MonitorRepository(session)
    monitor = await repository.get_by_id(monitor_id)

    if monitor is None:
        logger.info(
            "monitor_check_skipped_missing",
            extra={"monitor_id": str(monitor_id)},
        )
        return None

    if not monitor.is_active:
        logger.info(
            "monitor_check_skipped_inactive",
            extra={"monitor_id": str(monitor_id)},
        )
        return None

    await session.commit()
    engine = HttpCheckEngine(client)
    service = CheckExecutionService(
        session=session,
        engine=engine,
        realtime_publisher=realtime_publisher,
    )

    monitor_check = await service.execute(monitor)

    if dashboard_redis is not None:
        await invalidate_dashboard_cache(
            dashboard_redis,
            monitor.user_id,
        )

    return monitor_check


async def _execute_monitor_check_task(monitor_id: UUID) -> None:
    realtime_redis = create_async_redis_client()

    try:
        async with (
            async_session_factory() as session,
            httpx2.AsyncClient() as client,
        ):
            realtime_publisher = RedisRealtimePublisher(realtime_redis)
            monitor_check = await execute_monitor_check(
                monitor_id,
                session,
                client,
                realtime_publisher,
                realtime_redis,
            )
    finally:
        await realtime_redis.aclose()

    if monitor_check is not None:
        logger.info(
            "monitor_check_completed",
            extra={
                "monitor_id": str(monitor_id),
                "check_id": monitor_check.id,
                "success": monitor_check.success,
                "response_time_ms": monitor_check.response_time_ms,
            },
        )


@celery_app.task(name="app.workers.monitor_tasks.check_monitor")
def check_monitor(monitor_id: str) -> None:
    parsed_monitor_id = UUID(monitor_id)
    redis_client = create_redis_client()

    try:
        with acquire_monitor_lock(
            redis_client,
            parsed_monitor_id,
        ) as acquired:
            if not acquired:
                logger.info(
                    "monitor_check_skipped_locked",
                    extra={"monitor_id": monitor_id},
                )
                return
            run_worker_coroutine(
                _execute_monitor_check_task(parsed_monitor_id),
            )

    finally:
        redis_client.close()
