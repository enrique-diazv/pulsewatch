import pytest
from pydantic import ValidationError

from app.modules.dashboard.schemas import DashboardSummary


def test_dashboard_summary_accepts_valid_metrics() -> None:
    summary = DashboardSummary(
        total_monitors=12,
        operational_monitors=10,
        down_monitors=1,
        degraded_monitors=1,
        active_incidents=1,
        total_checks=1000,
        successful_checks=998,
        overall_uptime_percentage=99.8,
        average_response_time_ms=184.5,
    )

    assert summary.total_monitors == 12
    assert summary.overall_uptime_percentage == 99.8
    assert summary.average_response_time_ms == 184.5


def test_dashboard_summary_accepts_missing_check_metrics() -> None:
    summary = DashboardSummary(
        total_monitors=0,
        operational_monitors=0,
        down_monitors=0,
        degraded_monitors=0,
        active_incidents=0,
        total_checks=0,
        successful_checks=0,
    )

    assert summary.overall_uptime_percentage is None
    assert summary.average_response_time_ms is None


def test_dashboard_summary_rejects_invalid_values() -> None:
    with pytest.raises(ValidationError):
        DashboardSummary(
            total_monitors=-1,
            operational_monitors=0,
            down_monitors=0,
            degraded_monitors=0,
            active_incidents=0,
            total_checks=0,
            successful_checks=0,
            overall_uptime_percentage=101,
        )
