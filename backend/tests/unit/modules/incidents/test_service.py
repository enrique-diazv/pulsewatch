from datetime import UTC, datetime
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.database.models.incident import Incident
from app.database.models.monitor import Monitor
from app.database.models.monitor_check import MonitorCheck
from app.modules.incidents.enums import IncidentStatus
from app.modules.incidents.repository import IncidentRepository
from app.modules.incidents.service import IncidentDetectionService
from app.modules.monitors.enums import MonitorStatus

CHECKED_AT = datetime(2026, 8, 8, 22, 30, tzinfo=UTC)


def create_monitor(
    *,
    status: MonitorStatus,
    consecutive_failures: int = 0,
    consecutive_successes: int = 0,
) -> Monitor:
    return Monitor(
        id=uuid4(),
        user_id=uuid4(),
        name="Production API",
        url="https://api.example.com/health",
        interval_seconds=60,
        timeout_seconds=5,
        expected_status=200,
        status=status,
        failure_threshold=3,
        recovery_threshold=2,
        consecutive_failures=consecutive_failures,
        consecutive_successes=consecutive_successes,
        next_check_at=CHECKED_AT,
    )


def create_check(
    *,
    check_id: int,
    success: bool,
    error_type: str | None = None,
    error_message: str | None = None,
) -> MonitorCheck:
    return MonitorCheck(
        id=check_id,
        monitor_id=uuid4(),
        checked_at=CHECKED_AT,
        success=success,
        status_code=200 if success else None,
        response_time_ms=125,
        error_type=error_type,
        error_message=error_message,
    )


@pytest.mark.anyio
async def test_success_updates_monitor_without_incident() -> None:
    repository = AsyncMock(spec=IncidentRepository)
    service = IncidentDetectionService(repository)
    monitor = create_monitor(status=MonitorStatus.UNKNOWN)
    monitor_check = create_check(check_id=1, success=True)

    incident = await service.process_check(monitor, monitor_check)

    assert incident is None
    assert monitor.status is MonitorStatus.UP
    assert monitor.consecutive_failures == 0
    assert monitor.consecutive_successes == 1
    assert monitor.last_checked_at == CHECKED_AT
    repository.add.assert_not_awaited()
    repository.get_open_for_update.assert_not_awaited()


@pytest.mark.anyio
async def test_failure_threshold_opens_incident() -> None:
    repository = AsyncMock(spec=IncidentRepository)
    repository.add.side_effect = lambda incident: incident
    service = IncidentDetectionService(repository)
    monitor = create_monitor(
        status=MonitorStatus.UP,
        consecutive_failures=2,
    )
    monitor_check = create_check(
        check_id=42,
        success=False,
        error_type="TIMEOUT",
        error_message="Request timed out",
    )

    incident = await service.process_check(monitor, monitor_check)

    assert incident is repository.add.await_args.args[0]
    assert monitor.status is MonitorStatus.DOWN
    assert monitor.consecutive_failures == 3
    assert monitor.consecutive_successes == 0
    assert incident.monitor_id == monitor.id
    assert incident.started_at == CHECKED_AT
    assert incident.failure_reason == "Request timed out"
    assert incident.initial_check_id == 42


@pytest.mark.anyio
async def test_first_recovery_success_keeps_incident_open() -> None:
    repository = AsyncMock(spec=IncidentRepository)
    service = IncidentDetectionService(repository)
    monitor = create_monitor(status=MonitorStatus.DOWN)
    monitor_check = create_check(check_id=84, success=True)

    incident = await service.process_check(monitor, monitor_check)

    assert incident is None
    assert monitor.status is MonitorStatus.DOWN
    assert monitor.consecutive_successes == 1
    repository.get_open_for_update.assert_not_awaited()


@pytest.mark.anyio
async def test_recovery_threshold_resolves_open_incident() -> None:
    repository = AsyncMock(spec=IncidentRepository)
    monitor = create_monitor(
        status=MonitorStatus.DOWN,
        consecutive_successes=1,
    )
    open_incident = Incident(
        monitor_id=monitor.id,
        status=IncidentStatus.OPEN,
        started_at=CHECKED_AT,
        failure_reason="Request timed out",
        initial_check_id=42,
    )
    repository.get_open_for_update.return_value = open_incident
    service = IncidentDetectionService(repository)
    monitor_check = create_check(check_id=99, success=True)

    incident = await service.process_check(monitor, monitor_check)

    assert incident is open_incident
    assert monitor.status is MonitorStatus.UP
    assert monitor.consecutive_successes == 2
    assert open_incident.status is IncidentStatus.RESOLVED
    assert open_incident.resolved_at == CHECKED_AT
    assert open_incident.recovery_check_id == 99
