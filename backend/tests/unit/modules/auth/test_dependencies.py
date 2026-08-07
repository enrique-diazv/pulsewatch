from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.user import User
from app.modules.auth.dependencies import get_current_user
from app.security.tokens import InvalidAccessTokenError


@pytest.mark.anyio
async def test_get_current_user_returns_token_user() -> None:
    user_id = uuid4()
    user = User(
        id=user_id,
        email="user@example.com",
        password_hash="hashed-password",
    )
    session = AsyncMock(spec=AsyncSession)
    session.get.return_value = user
    credentials = HTTPAuthorizationCredentials(
        scheme="Bearer",
        credentials="valid-access-token",
    )

    with patch(
        "app.modules.auth.dependencies.decode_access_token",
        return_value=user_id,
    ):
        current_user = await get_current_user(
            credentials=credentials,
            session=session,
        )

    assert current_user is user
    session.get.assert_awaited_once_with(User, user_id)


@pytest.mark.anyio
async def test_get_current_user_rejects_invalid_token() -> None:
    session = AsyncMock(spec=AsyncSession)
    credentials = HTTPAuthorizationCredentials(
        scheme="Bearer",
        credentials="invalid-access-token",
    )

    with (
        patch(
            "app.modules.auth.dependencies.decode_access_token",
            side_effect=InvalidAccessTokenError,
        ),
        pytest.raises(HTTPException) as error,
    ):
        await get_current_user(
            credentials=credentials,
            session=session,
        )

    assert error.value.status_code == 401
    assert error.value.detail == "Invalid or missing access token"
    assert error.value.headers == {"WWW-Authenticate": "Bearer"}


@pytest.mark.anyio
async def test_get_current_user_rejects_missing_user() -> None:
    user_id = uuid4()
    session = AsyncMock(spec=AsyncSession)
    session.get.return_value = None
    credentials = HTTPAuthorizationCredentials(
        scheme="Bearer",
        credentials="valid-access-token",
    )

    with (
        patch(
            "app.modules.auth.dependencies.decode_access_token",
            return_value=user_id,
        ),
        pytest.raises(HTTPException) as error,
    ):
        await get_current_user(
            credentials=credentials,
            session=session,
        )

    assert error.value.status_code == 401
