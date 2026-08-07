from app.database.models import User, metadata


def test_user_model_has_expected_columns() -> None:
    table = User.__table__

    assert metadata.tables["users"] is table
    assert set(table.columns.keys()) == {
        "id",
        "email",
        "password_hash",
        "is_verified",
        "created_at",
        "updated_at",
    }
    assert list(table.primary_key.columns.keys()) == ["id"]
    assert table.c.email.unique is True
    assert table.c.email.nullable is False
    assert table.c.password_hash.nullable is False
    assert table.c.is_verified.nullable is False


def test_user_model_uses_bounded_string_columns() -> None:
    table = User.__table__

    assert table.c.email.type.length == 320
    assert table.c.password_hash.type.length == 255
