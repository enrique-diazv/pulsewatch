from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.user import User
from app.modules.auth.repository import UserRepository


@pytest.mark.anyio
async def test_get_by_email_returns_existing_user() -> None:
    user = User(
        email="user@example.com",
        password_hash="hashed-password",
    )
    result = MagicMock()
    result.scalar_one_or_none.return_value = user
    session = AsyncMock(spec=AsyncSession)
    session.execute.return_value = result
    repository = UserRepository(session)

    found_user = await repository.get_by_email("user@example.com")

    assert found_user is user
    session.execute.assert_awaited_once()


@pytest.mark.anyio
async def test_get_by_email_returns_none_when_user_does_not_exist() -> None:
    result = MagicMock()
    result.scalar_one_or_none.return_value = None
    session = AsyncMock(spec=AsyncSession)
    session.execute.return_value = result
    repository = UserRepository(session)

    found_user = await repository.get_by_email("missing@example.com")

    assert found_user is None


@pytest.mark.anyio
async def test_create_adds_and_flushes_user() -> None:
    session = AsyncMock(spec=AsyncSession)
    repository = UserRepository(session)

    user = await repository.create(
        email="user@example.com",
        password_hash="hashed-password",
    )

    assert user.email == "user@example.com"
    assert user.password_hash == "hashed-password"
    session.add.assert_called_once_with(user)
    session.flush.assert_awaited_once()


@pytest.mark.anyio
async def test_get_by_id_returns_user() -> None:
    user_id = uuid4()
    user = User(
        id=user_id,
        email="user@example.com",
        password_hash="hashed-password",
    )
    session = AsyncMock(spec=AsyncSession)
    session.get.return_value = user
    repository = UserRepository(session)

    found_user = await repository.get_by_id(user_id)

    assert found_user is user
    session.get.assert_awaited_once_with(User, user_id)
