from sqlalchemy import CheckConstraint

from app.database.models import Monitor, metadata


def test_monitor_model_has_expected_columns() -> None:
    table = Monitor.__table__

    assert metadata.tables["monitors"] is table
    assert set(table.columns.keys()) == {
        "id",
        "user_id",
        "name",
        "url",
        "method",
        "interval_seconds",
        "timeout_seconds",
        "expected_status",
        "status",
        "failure_threshold",
        "recovery_threshold",
        "consecutive_failures",
        "consecutive_successes",
        "is_active",
        "last_checked_at",
        "next_check_at",
        "created_at",
        "updated_at",
    }
    assert list(table.primary_key.columns.keys()) == ["id"]
    assert table.c.user_id.nullable is False
    assert table.c.next_check_at.nullable is False


def test_monitor_model_has_expected_indexes() -> None:
    index_names = {index.name for index in Monitor.__table__.indexes}

    assert index_names == {
        "ix_monitors_user_id",
        "ix_monitors_user_id_status",
        "ix_monitors_is_active_next_check_at",
    }


def test_monitor_model_has_database_constraints() -> None:
    constraints = {
        str(constraint.sqltext)
        for constraint in Monitor.__table__.constraints
        if isinstance(constraint, CheckConstraint)
    }

    assert "interval_seconds BETWEEN 30 AND 86400" in constraints
    assert "timeout_seconds BETWEEN 1 AND 60" in constraints
    assert "expected_status BETWEEN 100 AND 599" in constraints
    assert "failure_threshold BETWEEN 1 AND 10" in constraints
    assert "recovery_threshold BETWEEN 1 AND 10" in constraints
    assert "consecutive_failures >= 0" in constraints
    assert "consecutive_successes >= 0" in constraints
