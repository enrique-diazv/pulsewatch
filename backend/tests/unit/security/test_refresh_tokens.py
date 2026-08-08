from app.security.refresh_tokens import (
    generate_refresh_token,
    hash_refresh_token,
)


def test_generate_refresh_token_returns_unique_values() -> None:
    first_token = generate_refresh_token()
    second_token = generate_refresh_token()

    assert first_token != second_token
    assert len(first_token) >= 64
    assert len(second_token) >= 64


def test_hash_refresh_token_is_deterministic() -> None:
    token = "example-refresh-token"

    first_hash = hash_refresh_token(token)
    second_hash = hash_refresh_token(token)

    assert first_hash == second_hash
    assert len(first_hash) == 64


def test_hash_refresh_token_does_not_expose_original_token() -> None:
    token = "sensitive-refresh-token"

    token_hash = hash_refresh_token(token)

    assert token != token_hash
    assert token not in token_hash
