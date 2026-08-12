from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.checks.repository import (
    MonitorCheckMetricsSummary,
    MonitorCheckRepository,
)
from app.modules.checks.service import MonitorMetricsService
from app.modules.metrics.repository import (
    HourlyMetricRepository,
    HourlyMetricSummary,
)

NOW = datetime(2026, 8, 9, 18, 0, tzinfo=UTC)


@pytest.mark.anyio
async def test_summarize_calculates_metrics_for_range() -> None:
    session = AsyncMock(spec=AsyncSession)
    repository = AsyncMock(spec=MonitorCheckRepository)
    repository.summarize_for_monitor.return_value = MonitorCheckMetricsSummary(
        total_checks=10,
        successful_checks=8,
        average_response_time_ms=147.556,
    )
    monitor_id = uuid4()
    service = MonitorMetricsService(
        session,
        repository=repository,
        clock=lambda: NOW,
    )

    metrics = await service.summarize(
        monitor_id,
        "24h",
    )

    assert metrics.range == "24h"
    assert metrics.from_timestamp == NOW - timedelta(hours=24)
    assert metrics.to_timestamp == NOW
    assert metrics.total_checks == 10
    assert metrics.successful_checks == 8
    assert metrics.failed_checks == 2
    assert metrics.uptime_percentage == 80.0
    assert metrics.average_response_time_ms == 147.56
    repository.summarize_for_monitor.assert_awaited_once_with(
        monitor_id,
        from_timestamp=NOW - timedelta(hours=24),
        to_timestamp=NOW,
    )


@pytest.mark.anyio
@pytest.mark.anyio
async def test_summarize_returns_null_metrics_without_checks() -> None:
    session = AsyncMock(spec=AsyncSession)
    repository = AsyncMock(
        spec=MonitorCheckRepository,
    )
    hourly_repository = AsyncMock(
        spec=HourlyMetricRepository,
    )
    empty_summary = MonitorCheckMetricsSummary(
        total_checks=0,
        successful_checks=0,
        average_response_time_ms=None,
    )
    repository.summarize_for_monitor.return_value = empty_summary
    hourly_repository.summarize_for_monitor.return_value = HourlyMetricSummary(
        total_checks=0,
        successful_checks=0,
        average_response_time_ms=None,
    )
    monitor_id = uuid4()
    service = MonitorMetricsService(
        session,
        repository=repository,
        hourly_repository=hourly_repository,
        clock=lambda: NOW,
    )

    metrics = await service.summarize(
        monitor_id,
        "30d",
    )

    assert metrics.from_timestamp == (NOW - timedelta(days=30))
    assert metrics.total_checks == 0
    assert metrics.successful_checks == 0
    assert metrics.failed_checks == 0
    assert metrics.uptime_percentage is None
    assert metrics.average_response_time_ms is None

    hourly_repository.summarize_for_monitor.assert_awaited_once_with(
        monitor_id,
        from_hour=NOW - timedelta(days=30),
        to_hour=NOW - timedelta(hours=1),
    )
    repository.summarize_for_monitor.assert_awaited_once_with(
        monitor_id,
        from_timestamp=NOW - timedelta(hours=1),
        to_timestamp=NOW,
    )


@pytest.mark.anyio
async def test_summarize_combines_hourly_and_recent_raw_metrics() -> None:
    session = AsyncMock(spec=AsyncSession)
    repository = AsyncMock(
        spec=MonitorCheckRepository,
    )
    hourly_repository = AsyncMock(
        spec=HourlyMetricRepository,
    )
    hourly_repository.summarize_for_monitor.return_value = HourlyMetricSummary(
        total_checks=90,
        successful_checks=89,
        average_response_time_ms=100.0,
    )
    repository.summarize_for_monitor.return_value = MonitorCheckMetricsSummary(
        total_checks=10,
        successful_checks=9,
        average_response_time_ms=200.0,
    )
    monitor_id = uuid4()
    service = MonitorMetricsService(
        session,
        repository=repository,
        hourly_repository=hourly_repository,
        clock=lambda: NOW,
    )

    metrics = await service.summarize(
        monitor_id,
        "7d",
    )

    assert metrics.total_checks == 100
    assert metrics.successful_checks == 98
    assert metrics.failed_checks == 2
    assert metrics.uptime_percentage == 98.0
    assert metrics.average_response_time_ms == 110.0

    hourly_repository.summarize_for_monitor.assert_awaited_once_with(
        monitor_id,
        from_hour=NOW - timedelta(days=7),
        to_hour=NOW - timedelta(hours=1),
    )
    repository.summarize_for_monitor.assert_awaited_once_with(
        monitor_id,
        from_timestamp=NOW - timedelta(hours=1),
        to_timestamp=NOW,
    )
