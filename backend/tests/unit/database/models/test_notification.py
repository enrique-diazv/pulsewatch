from sqlalchemy import CheckConstraint, UniqueConstraint

from app.database.models import Notification, metadata


def test_notification_model_has_expected_columns() -> None:
    table = Notification.__table__

    assert metadata.tables["notifications"] is table
    assert set(table.columns.keys()) == {
        "id",
        "user_id",
        "incident_id",
        "type",
        "status",
        "attempt_count",
        "last_error",
        "sent_at",
        "created_at",
    }
    assert list(table.primary_key.columns.keys()) == ["id"]
    assert table.c.user_id.nullable is False
    assert table.c.incident_id.nullable is False
    assert table.c.type.nullable is False
    assert table.c.status.nullable is False
    assert table.c.attempt_count.nullable is False
    assert table.c.last_error.nullable is True
    assert table.c.last_error.type.length == 500
    assert table.c.sent_at.nullable is True

    user_foreign_key = next(iter(table.c.user_id.foreign_keys))
    incident_foreign_key = next(iter(table.c.incident_id.foreign_keys))

    assert user_foreign_key.ondelete == "CASCADE"
    assert incident_foreign_key.ondelete == "CASCADE"


def test_notification_model_has_delivery_indexes() -> None:
    indexes = {index.name: index for index in Notification.__table__.indexes}

    assert set(indexes) == {
        "ix_notifications_status_created_at",
        "ix_notifications_user_id_created_at",
    }


def test_notification_model_has_delivery_constraints() -> None:
    constraints = Notification.__table__.constraints
    check_constraint_names = {
        constraint.name
        for constraint in constraints
        if isinstance(constraint, CheckConstraint)
    }
    unique_constraint_names = {
        constraint.name
        for constraint in constraints
        if isinstance(constraint, UniqueConstraint)
    }

    assert "notification_attempt_count_nonnegative" in (check_constraint_names)
    assert "notification_delivery_consistency" in (check_constraint_names)
    assert "uq_notifications_incident_id_type" in (unique_constraint_names)
