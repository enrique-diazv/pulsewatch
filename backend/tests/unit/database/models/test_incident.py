from sqlalchemy import CheckConstraint

from app.database.models import Incident, metadata


def test_incident_model_has_expected_columns() -> None:
    table = Incident.__table__

    assert metadata.tables["incidents"] is table
    assert set(table.columns.keys()) == {
        "id",
        "monitor_id",
        "started_at",
        "resolved_at",
        "status",
        "failure_reason",
        "initial_check_id",
        "recovery_check_id",
    }
    assert list(table.primary_key.columns.keys()) == ["id"]
    assert table.c.monitor_id.nullable is False
    assert table.c.resolved_at.nullable is True
    assert table.c.failure_reason.nullable is False
    assert table.c.failure_reason.type.length == 500
    assert table.c.initial_check_id.nullable is False
    assert table.c.recovery_check_id.nullable is True


def test_incident_model_has_expected_indexes() -> None:
    indexes = {index.name: index for index in Incident.__table__.indexes}

    assert set(indexes) == {
        "ix_incidents_monitor_id_started_at",
        "uq_incidents_open_monitor_id",
    }
    assert indexes["uq_incidents_open_monitor_id"].unique is True


def test_incident_model_has_resolution_constraint() -> None:
    constraint_names = {
        constraint.name
        for constraint in Incident.__table__.constraints
        if isinstance(constraint, CheckConstraint)
    }

    assert "incident_resolution_consistency" in constraint_names
