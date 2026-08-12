from sqlalchemy import CheckConstraint

from app.database.models import (
    MonitorHourlyMetric,
    metadata,
)


def test_hourly_metric_model_has_expected_columns() -> None:
    table = MonitorHourlyMetric.__table__

    assert metadata.tables["monitor_hourly_metrics"] is table
    assert set(table.columns.keys()) == {
        "monitor_id",
        "hour",
        "total_checks",
        "successful_checks",
        "failed_checks",
        "average_response_time_ms",
        "min_response_time_ms",
        "max_response_time_ms",
        "uptime_percentage",
        "updated_at",
    }
    assert list(table.primary_key.columns.keys()) == [
        "monitor_id",
        "hour",
    ]

    monitor_foreign_key = next(
        iter(table.c.monitor_id.foreign_keys),
    )

    assert monitor_foreign_key.ondelete == "CASCADE"


def test_hourly_metric_model_has_retention_index() -> None:
    index_names = {index.name for index in MonitorHourlyMetric.__table__.indexes}

    assert index_names == {
        "ix_monitor_hourly_metrics_hour",
    }


def test_hourly_metric_model_has_consistency_constraints() -> None:
    constraint_names = {
        constraint.name
        for constraint in MonitorHourlyMetric.__table__.constraints
        if isinstance(constraint, CheckConstraint)
    }

    assert constraint_names == {
        "hourly_metrics_total_checks_positive",
        "hourly_metrics_check_counts_consistent",
        "hourly_metrics_check_counts_nonnegative",
        "hourly_metrics_response_times_valid",
        "hourly_metrics_uptime_percentage_range",
    }
