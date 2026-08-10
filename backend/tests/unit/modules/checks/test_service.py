from datetime import UTC, datetime
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.incident import Incident
from app.database.models.monitor import Monitor
from app.modules.checks.engine import HttpCheckEngine
from app.modules.checks.repository import MonitorCheckRepository
from app.modules.checks.results import CheckErrorType, HttpCheckResult
from app.modules.checks.service import CheckExecutionService
from app.modules.incidents.enums import IncidentStatus
from app.modules.incidents.service import IncidentDetectionService
from app.modules.monitors.enums import MonitorStatus
from app.modules.realtime.events import (
    RealtimeEventType,
    RealtimePublisher,
)


def create_monitor() -> Monitor:
    return Monitor(
        id=uuid4(),
        user_id=uuid4(),
        name="Production API",
        url="https://api.example.com/health",
        interval_seconds=60,
        timeout_seconds=5,
        expected_status=200,
        status=MonitorStatus.UNKNOWN,
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


@pytest.mark.anyio
async def test_execute_publishes_monitor_and_incident_events() -> None:
    session = AsyncMock(spec=AsyncSession)
    engine = AsyncMock(spec=HttpCheckEngine)
    repository = AsyncMock(spec=MonitorCheckRepository)
    incident_service = AsyncMock(spec=IncidentDetectionService)
    realtime_publisher = AsyncMock(spec=RealtimePublisher)
    incident = Incident(
        id=uuid4(),
        monitor_id=uuid4(),
        status=IncidentStatus.OPEN,
        failure_reason="Service unavailable",
        initial_check_id=321,
    )

    def add_monitor_check(monitor_check: object) -> object:
        monitor_check.id = 321
        return monitor_check

    async def process_check(
        monitor: Monitor,
        monitor_check: object,
    ) -> Incident:
        monitor.status = MonitorStatus.DOWN
        incident.monitor_id = monitor.id

        return incident

    repository.add.side_effect = add_monitor_check
    incident_service.process_check.side_effect = process_check
    engine.execute.return_value = HttpCheckResult(
        success=False,
        status_code=503,
        response_time_ms=250,
    )
    service = CheckExecutionService(
        session=session,
        engine=engine,
        repository=repository,
        incident_service=incident_service,
        realtime_publisher=realtime_publisher,
    )
    monitor = create_monitor()

    await service.execute(monitor)

    assert realtime_publisher.publish.await_count == 2

    monitor_event = realtime_publisher.publish.await_args_list[0].args[1]
    incident_event = realtime_publisher.publish.await_args_list[1].args[1]

    assert monitor_event.type == RealtimeEventType.MONITOR_UPDATED
    assert monitor_event.monitor_id == monitor.id
    assert monitor_event.monitor_status == MonitorStatus.DOWN
    assert monitor_event.check_id == 321

    assert incident_event.type == RealtimeEventType.INCIDENT_OPENED
    assert incident_event.incident_id == incident.id


@pytest.mark.anyio
async def test_realtime_failure_does_not_fail_stored_check() -> None:
    session = AsyncMock(spec=AsyncSession)
    engine = AsyncMock(spec=HttpCheckEngine)
    repository = AsyncMock(spec=MonitorCheckRepository)
    incident_service = AsyncMock(spec=IncidentDetectionService)
    realtime_publisher = AsyncMock(spec=RealtimePublisher)

    def add_monitor_check(monitor_check: object) -> object:
        monitor_check.id = 654
        return monitor_check

    repository.add.side_effect = add_monitor_check
    incident_service.process_check.return_value = None
    realtime_publisher.publish.side_effect = RuntimeError("Redis unavailable")
    engine.execute.return_value = HttpCheckResult(
        success=True,
        status_code=200,
        response_time_ms=100,
    )
    service = CheckExecutionService(
        session=session,
        engine=engine,
        repository=repository,
        incident_service=incident_service,
        realtime_publisher=realtime_publisher,
    )
    monitor = create_monitor()

    monitor_check = await service.execute(monitor)

    assert monitor_check.id == 654
    session.commit.assert_awaited_once()
    realtime_publisher.publish.assert_awaited_once()
