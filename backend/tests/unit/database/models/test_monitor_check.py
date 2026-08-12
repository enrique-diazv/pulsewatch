from sqlalchemy import CheckConstraint

from app.database.models import MonitorCheck, metadata


def test_monitor_check_model_has_expected_columns() -> None:
    table = MonitorCheck.__table__

    assert metadata.tables["monitor_checks"] is table
    assert set(table.columns.keys()) == {
        "id",
        "monitor_id",
        "checked_at",
        "success",
        "status_code",
        "response_time_ms",
        "error_type",
        "error_message",
    }
    assert list(table.primary_key.columns.keys()) == ["id"]
    assert table.c.monitor_id.nullable is False
    assert table.c.status_code.nullable is True
    assert table.c.error_type.type.length == 64
    assert table.c.error_message.type.length == 500


def test_monitor_check_model_has_history_index() -> None:
    indexes = list(MonitorCheck.__table__.indexes)

    assert len(indexes) == 1

    history_index = indexes[0]

    assert history_index.name == ("ix_monitor_checks_monitor_id_checked_at_id")
    assert [str(expression) for expression in history_index.expressions] == [
        "monitor_checks.monitor_id",
        "monitor_checks.checked_at DESC",
        "monitor_checks.id DESC",
    ]


def test_monitor_check_model_has_database_constraints() -> None:
    constraints = {
        str(constraint.sqltext)
        for constraint in MonitorCheck.__table__.constraints
        if isinstance(constraint, CheckConstraint)
    }

    assert "response_time_ms >= 0" in constraints
    assert "status_code IS NULL OR status_code BETWEEN 100 AND 599" in constraints
