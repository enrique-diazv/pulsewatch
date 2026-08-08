from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.refresh_token import RefreshToken
from app.modules.auth.refresh_token_repository import (
    RefreshTokenRepository,
)


@pytest.mark.anyio
async def test_get_active_by_hash_returns_token() -> None:
    refresh_token = RefreshToken(
        user_id=uuid4(),
        token_hash="a" * 64,
        expires_at=datetime.now(UTC) + timedelta(days=30),
    )
    result = MagicMock()
    result.scalar_one_or_none.return_value = refresh_token
    session = AsyncMock(spec=AsyncSession)
    session.execute.return_value = result
    repository = RefreshTokenRepository(session)

    found_token = await repository.get_active_by_hash("a" * 64)

    assert found_token is refresh_token
    session.execute.assert_awaited_once()


@pytest.mark.anyio
async def test_create_adds_and_flushes_refresh_token() -> None:
    session = AsyncMock(spec=AsyncSession)
    repository = RefreshTokenRepository(session)
    user_id = uuid4()
    expires_at = datetime.now(UTC) + timedelta(days=30)

    refresh_token = await repository.create(
        user_id=user_id,
        token_hash="b" * 64,
        expires_at=expires_at,
    )

    assert refresh_token.user_id == user_id
    assert refresh_token.token_hash == "b" * 64
    assert refresh_token.expires_at == expires_at
    session.add.assert_called_once_with(refresh_token)
    session.flush.assert_awaited_once()


def test_revoke_marks_refresh_token_as_revoked() -> None:
    repository = RefreshTokenRepository(AsyncMock(spec=AsyncSession))
    refresh_token = RefreshToken(
        user_id=uuid4(),
        token_hash="c" * 64,
        expires_at=datetime.now(UTC) + timedelta(days=30),
    )
    revoked_at = datetime.now(UTC)

    repository.revoke(
        refresh_token,
        revoked_at=revoked_at,
    )

    assert refresh_token.revoked_at == revoked_at
