from app.security.passwords import hash_password, verify_password


def test_hash_and_verify_password() -> None:
    plain_password = "correct horse battery staple"

    hashed_password = hash_password(plain_password)

    assert hashed_password != plain_password
    assert hashed_password.startswith("$argon2id$")
    assert verify_password(plain_password, hashed_password) is True
    assert verify_password("incorrect-password", hashed_password) is False


def test_hash_password_uses_unique_salt() -> None:
    plain_password = "same-password"

    first_hash = hash_password(plain_password)
    second_hash = hash_password(plain_password)

    assert first_hash != second_hash
