from datetime import UTC, datetime
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.monitor import Monitor
from app.modules.checks.engine import HttpCheckEngine
from app.modules.checks.repository import MonitorCheckRepository
from app.modules.checks.results import CheckErrorType, HttpCheckResult
from app.modules.checks.service import CheckExecutionService
from app.modules.incidents.service import IncidentDetectionService


def create_monitor() -> Monitor:
    return Monitor(
        id=uuid4(),
        user_id=uuid4(),
        name="Production API",
        url="https://api.example.com/health",
        interval_seconds=60,
        timeout_seconds=5,
        expected_status=200,
        next_check_at=datetime(2026, 8, 8, tzinfo=UTC),
    )


@pytest.mark.anyio
async def test_execute_stores_successful_result() -> None:
    session = AsyncMock(spec=AsyncSession)
    engine = AsyncMock(spec=HttpCheckEngine)
    repository = AsyncMock(spec=MonitorCheckRepository)
    incident_service = AsyncMock(spec=IncidentDetectionService)
    repository.add.side_effect = lambda monitor_check: monitor_check
    engine.execute.return_value = HttpCheckResult(
        success=True,
        status_code=200,
        response_time_ms=125,
    )
    service = CheckExecutionService(
        session=session,
        engine=engine,
        repository=repository,
        incident_service=incident_service,
    )
    monitor = create_monitor()

    monitor_check = await service.execute(monitor)

    assert monitor_check.monitor_id == monitor.id
    assert monitor_check.success is True
    assert monitor_check.status_code == 200
    assert monitor_check.response_time_ms == 125
    assert monitor_check.error_type is None
    engine.execute.assert_awaited_once_with(
        url=monitor.url,
        timeout_seconds=monitor.timeout_seconds,
        expected_status=monitor.expected_status,
    )
    repository.add.assert_awaited_once_with(monitor_check)
    incident_service.process_check.assert_awaited_once_with(
        monitor,
        monitor_check,
    )
    session.commit.assert_awaited_once()
    assert session.refresh.await_count == 2
    session.refresh.assert_any_await(
        monitor,
        with_for_update=True,
    )
    session.refresh.assert_any_await(monitor_check)


@pytest.mark.anyio
async def test_execute_stores_classified_failure() -> None:
    session = AsyncMock(spec=AsyncSession)
    engine = AsyncMock(spec=HttpCheckEngine)
    repository = AsyncMock(spec=MonitorCheckRepository)
    incident_service = AsyncMock(spec=IncidentDetectionService)
    repository.add.side_effect = lambda monitor_check: monitor_check
    engine.execute.return_value = HttpCheckResult(
        success=False,
        status_code=None,
        response_time_ms=5000,
        error_type=CheckErrorType.TIMEOUT,
        error_message="Request timed out",
    )
    service = CheckExecutionService(
        session=session,
        engine=engine,
        repository=repository,
        incident_service=incident_service,
    )
    monitor = create_monitor()

    monitor_check = await service.execute(monitor)

    assert monitor_check.success is False
    assert monitor_check.status_code is None
    assert monitor_check.error_type == "TIMEOUT"
    assert monitor_check.error_message == "Request timed out"
    incident_service.process_check.assert_awaited_once_with(
        monitor,
        monitor_check,
    )
    session.commit.assert_awaited_once()
    assert session.refresh.await_count == 2
    session.refresh.assert_any_await(
        monitor,
        with_for_update=True,
    )
    session.refresh.assert_any_await(monitor_check)
