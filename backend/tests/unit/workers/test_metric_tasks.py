from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.modules.metrics.retention import (
    MonitorCheckRetentionService,
)
from app.modules.metrics.service import (
    HourlyMetricAggregationService,
)
from app.workers.metric_tasks import (
    _purge_expired_monitor_checks_task,
    aggregate_closed_hour,
)


@pytest.mark.anyio
async def test_purge_task_uses_retention_service() -> None:
    session = AsyncMock(spec=AsyncSession)
    service = AsyncMock(
        spec=MonitorCheckRetentionService,
    )
    service.purge.return_value = 250
    settings = Settings(
        _env_file=None,
        database_password="test-password",
        jwt_secret_key=("test-jwt-secret-key-with-at-least-32-characters"),
    )
    session_context = AsyncMock()
    session_context.__aenter__.return_value = session
    session_context.__aexit__.return_value = None

    with (
        patch(
            "app.workers.metric_tasks.get_settings",
            return_value=settings,
        ),
        patch(
            "app.workers.metric_tasks.async_session_factory",
            return_value=session_context,
        ),
        patch(
            "app.workers.metric_tasks.MonitorCheckRetentionService",
            return_value=service,
        ) as service_class,
        patch(
            "app.workers.metric_tasks.logger",
        ) as logger,
    ):
        await _purge_expired_monitor_checks_task()

    service_class.assert_called_once_with(
        session,
        settings,
    )
    service.purge.assert_awaited_once_with()
    logger.info.assert_called_once_with(
        "monitor_check_retention_completed",
        extra={"deleted_checks": 250},
    )


@pytest.mark.anyio
async def test_aggregate_closed_hour_uses_aggregation_service() -> None:
    session = AsyncMock(spec=AsyncSession)
    service = AsyncMock(
        spec=HourlyMetricAggregationService,
    )
    service.aggregate_previous_hour.return_value = 4
    now = datetime(
        2026,
        8,
        12,
        12,
        5,
        tzinfo=UTC,
    )

    with patch(
        "app.workers.metric_tasks.HourlyMetricAggregationService",
        return_value=service,
    ) as service_class:
        affected_rows = await aggregate_closed_hour(
            session,
            now,
        )

    assert affected_rows == 4
    service_class.assert_called_once_with(session)
    service.aggregate_previous_hour.assert_awaited_once_with(
        now,
    )
