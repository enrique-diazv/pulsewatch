from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.database.models.refresh_token import RefreshToken
from app.modules.auth.exceptions import InvalidRefreshTokenError
from app.modules.auth.refresh_token_repository import (
    RefreshTokenRepository,
)
from app.modules.auth.refresh_token_service import RefreshTokenService


def create_test_settings() -> Settings:
    return Settings(
        _env_file=None,
        database_password="test-password",
        jwt_secret_key="test-jwt-secret-key-with-at-least-32-characters",
        refresh_token_expire_days=30,
    )


@pytest.mark.anyio
async def test_issue_stores_hash_and_returns_raw_token() -> None:
    session = AsyncMock(spec=AsyncSession)
    repository = AsyncMock(spec=RefreshTokenRepository)
    service = RefreshTokenService(
        session=session,
        settings=create_test_settings(),
        repository=repository,
    )
    user_id = uuid4()
    issued_at = datetime(2026, 8, 7, tzinfo=UTC)

    with (
        patch(
            "app.modules.auth.refresh_token_service.generate_refresh_token",
            return_value="raw-refresh-token",
        ),
        patch(
            "app.modules.auth.refresh_token_service.hash_refresh_token",
            return_value="a" * 64,
        ),
    ):
        raw_token = await service.issue(
            user_id,
            now=issued_at,
        )

    assert raw_token == "raw-refresh-token"
    repository.create.assert_awaited_once_with(
        user_id=user_id,
        token_hash="a" * 64,
        expires_at=issued_at + timedelta(days=30),
    )
    session.commit.assert_awaited_once()


@pytest.mark.anyio
async def test_rotate_revokes_old_token_and_returns_new_token() -> None:
    session = AsyncMock(spec=AsyncSession)
    repository = AsyncMock(spec=RefreshTokenRepository)
    user_id = uuid4()
    stored_token = RefreshToken(
        user_id=user_id,
        token_hash="a" * 64,
        expires_at=datetime(2026, 9, 6, tzinfo=UTC),
    )
    repository.get_active_by_hash.return_value = stored_token
    service = RefreshTokenService(
        session=session,
        settings=create_test_settings(),
        repository=repository,
    )
    rotated_at = datetime(2026, 8, 8, tzinfo=UTC)

    with (
        patch(
            "app.modules.auth.refresh_token_service.generate_refresh_token",
            return_value="new-raw-refresh-token",
        ),
        patch(
            "app.modules.auth.refresh_token_service.hash_refresh_token",
            side_effect=["a" * 64, "b" * 64],
        ),
    ):
        rotation = await service.rotate(
            "old-raw-refresh-token",
            now=rotated_at,
        )

    repository.get_active_by_hash.assert_awaited_once_with("a" * 64)
    repository.revoke.assert_called_once_with(
        stored_token,
        revoked_at=rotated_at,
    )
    repository.create.assert_awaited_once_with(
        user_id=user_id,
        token_hash="b" * 64,
        expires_at=rotated_at + timedelta(days=30),
    )
    session.commit.assert_awaited_once()
    assert rotation.user_id == user_id
    assert rotation.token == "new-raw-refresh-token"


@pytest.mark.anyio
async def test_rotate_rejects_invalid_refresh_token() -> None:
    session = AsyncMock(spec=AsyncSession)
    repository = AsyncMock(spec=RefreshTokenRepository)
    repository.get_active_by_hash.return_value = None
    service = RefreshTokenService(
        session=session,
        settings=create_test_settings(),
        repository=repository,
    )

    with (
        patch(
            "app.modules.auth.refresh_token_service.hash_refresh_token",
            return_value="a" * 64,
        ),
        pytest.raises(InvalidRefreshTokenError),
    ):
        await service.rotate("invalid-refresh-token")

    repository.revoke.assert_not_called()
    repository.create.assert_not_awaited()
    session.commit.assert_not_awaited()


@pytest.mark.anyio
async def test_revoke_marks_active_token_as_revoked() -> None:
    session = AsyncMock(spec=AsyncSession)
    repository = AsyncMock(spec=RefreshTokenRepository)
    stored_token = RefreshToken(
        user_id=uuid4(),
        token_hash="a" * 64,
        expires_at=datetime(2026, 9, 6, tzinfo=UTC),
    )
    repository.get_active_by_hash.return_value = stored_token
    service = RefreshTokenService(
        session=session,
        settings=create_test_settings(),
        repository=repository,
    )
    revoked_at = datetime(2026, 8, 8, tzinfo=UTC)

    with patch(
        "app.modules.auth.refresh_token_service.hash_refresh_token",
        return_value="a" * 64,
    ):
        was_revoked = await service.revoke(
            "raw-refresh-token",
            now=revoked_at,
        )

    assert was_revoked is True
    repository.revoke.assert_called_once_with(
        stored_token,
        revoked_at=revoked_at,
    )
    session.commit.assert_awaited_once()


@pytest.mark.anyio
async def test_revoke_is_idempotent_for_invalid_token() -> None:
    session = AsyncMock(spec=AsyncSession)
    repository = AsyncMock(spec=RefreshTokenRepository)
    repository.get_active_by_hash.return_value = None
    service = RefreshTokenService(
        session=session,
        settings=create_test_settings(),
        repository=repository,
    )

    with patch(
        "app.modules.auth.refresh_token_service.hash_refresh_token",
        return_value="a" * 64,
    ):
        was_revoked = await service.revoke("invalid-refresh-token")

    assert was_revoked is False
    repository.revoke.assert_not_called()
    session.commit.assert_not_awaited()
