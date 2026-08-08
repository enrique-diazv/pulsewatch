from app.database.models import RefreshToken, metadata


def test_refresh_token_model_has_expected_columns() -> None:
    table = RefreshToken.__table__

    assert metadata.tables["refresh_tokens"] is table
    assert set(table.columns.keys()) == {
        "id",
        "user_id",
        "token_hash",
        "expires_at",
        "revoked_at",
        "created_at",
    }
    assert list(table.primary_key.columns.keys()) == ["id"]
    assert table.c.user_id.nullable is False
    assert table.c.token_hash.nullable is False
    assert table.c.token_hash.unique is True
    assert table.c.expires_at.nullable is False
    assert table.c.revoked_at.nullable is True


def test_refresh_token_model_has_user_foreign_key() -> None:
    table = RefreshToken.__table__
    foreign_key = next(iter(table.c.user_id.foreign_keys))

    assert foreign_key.target_fullname == "users.id"
    assert foreign_key.ondelete == "CASCADE"
    assert table.c.user_id.index is True
    assert table.c.token_hash.type.length == 64
