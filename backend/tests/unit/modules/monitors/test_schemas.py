from datetime import UTC, datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.database.models.monitor import Monitor
from app.modules.monitors.enums import HttpMethod, MonitorStatus
from app.modules.monitors.schemas import MonitorCreate, MonitorResponse, MonitorUpdate


def test_monitor_create_accepts_valid_configuration() -> None:
    request = MonitorCreate(
        name="  Production API  ",
        url="https://api.example.com/health",
    )

    assert request.name == "Production API"
    assert str(request.url) == "https://api.example.com/health"
    assert request.method is HttpMethod.GET
    assert request.interval_seconds == 60
    assert request.timeout_seconds == 5
    assert request.expected_status == 200
    assert request.failure_threshold == 3
    assert request.recovery_threshold == 2


def test_monitor_create_rejects_unsupported_url_scheme() -> None:
    with pytest.raises(ValidationError):
        MonitorCreate(
            name="FTP server",
            url="ftp://example.com/file",
        )


def test_monitor_create_rejects_values_outside_limits() -> None:
    with pytest.raises(ValidationError):
        MonitorCreate(
            name="Invalid monitor",
            url="https://example.com",
            interval_seconds=29,
            timeout_seconds=61,
            expected_status=99,
            failure_threshold=0,
            recovery_threshold=11,
        )


def test_monitor_response_excludes_ownership_and_internal_counters() -> None:
    timestamp = datetime(2026, 8, 8, tzinfo=UTC)
    monitor = Monitor(
        id=uuid4(),
        user_id=uuid4(),
        name="Production API",
        url="https://api.example.com/health",
        method=HttpMethod.GET,
        interval_seconds=60,
        timeout_seconds=5,
        expected_status=200,
        status=MonitorStatus.UNKNOWN,
        failure_threshold=3,
        recovery_threshold=2,
        consecutive_failures=0,
        consecutive_successes=0,
        is_active=True,
        last_checked_at=None,
        next_check_at=timestamp,
        created_at=timestamp,
        updated_at=timestamp,
    )

    response = MonitorResponse.model_validate(monitor)
    response_data = response.model_dump()

    assert response_data["name"] == "Production API"
    assert "user_id" not in response_data
    assert "consecutive_failures" not in response_data
    assert "consecutive_successes" not in response_data


def test_monitor_update_accepts_partial_changes() -> None:
    request = MonitorUpdate(
        name="  Updated API  ",
        timeout_seconds=10,
    )

    assert request.name == "Updated API"
    assert request.timeout_seconds == 10
    assert request.interval_seconds is None


def test_monitor_update_rejects_empty_body() -> None:
    with pytest.raises(ValidationError):
        MonitorUpdate()


def test_monitor_update_rejects_invalid_values() -> None:
    with pytest.raises(ValidationError):
        MonitorUpdate(
            interval_seconds=10,
            expected_status=700,
        )
