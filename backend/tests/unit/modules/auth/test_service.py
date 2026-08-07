from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.user import User
from app.modules.auth.exceptions import (
    EmailAlreadyRegisteredError,
    InvalidCredentialsError,
)
from app.modules.auth.repository import UserRepository
from app.modules.auth.schemas import LoginRequest, RegisterRequest
from app.modules.auth.service import AuthService


@pytest.mark.anyio
async def test_register_creates_user_with_normalized_email() -> None:
    session = AsyncMock(spec=AsyncSession)
    repository = AsyncMock(spec=UserRepository)
    repository.get_by_email.return_value = None
    user = User(
        email="user@example.com",
        password_hash="hashed-password",
    )
    repository.create.return_value = user
    service = AuthService(session=session, repository=repository)
    request = RegisterRequest(
        email="User@Example.com",
        password="correct horse battery staple",
    )

    with patch(
        "app.modules.auth.service.hash_password",
        return_value="hashed-password",
    ) as password_hasher:
        created_user = await service.register(request)

    assert created_user is user
    repository.get_by_email.assert_awaited_once_with("user@example.com")
    repository.create.assert_awaited_once_with(
        email="user@example.com",
        password_hash="hashed-password",
    )
    password_hasher.assert_called_once_with(request.password)
    session.commit.assert_awaited_once()
    session.refresh.assert_awaited_once_with(user)


@pytest.mark.anyio
async def test_register_rejects_existing_email() -> None:
    session = AsyncMock(spec=AsyncSession)
    repository = AsyncMock(spec=UserRepository)
    repository.get_by_email.return_value = User(
        email="user@example.com",
        password_hash="hashed-password",
    )
    service = AuthService(session=session, repository=repository)
    request = RegisterRequest(
        email="user@example.com",
        password="correct horse battery staple",
    )

    with pytest.raises(EmailAlreadyRegisteredError):
        await service.register(request)

    repository.create.assert_not_awaited()
    session.commit.assert_not_awaited()


@pytest.mark.anyio
async def test_register_rolls_back_on_unique_constraint_conflict() -> None:
    session = AsyncMock(spec=AsyncSession)
    repository = AsyncMock(spec=UserRepository)
    repository.get_by_email.return_value = None
    repository.create.side_effect = IntegrityError(
        "INSERT INTO users",
        {},
        Exception("duplicate email"),
    )
    service = AuthService(session=session, repository=repository)
    request = RegisterRequest(
        email="user@example.com",
        password="correct horse battery staple",
    )

    with (
        patch(
            "app.modules.auth.service.hash_password",
            return_value="hashed-password",
        ),
        pytest.raises(EmailAlreadyRegisteredError),
    ):
        await service.register(request)

    session.rollback.assert_awaited_once()
    session.commit.assert_not_awaited()


@pytest.mark.anyio
async def test_authenticate_returns_user_for_valid_credentials() -> None:
    session = AsyncMock(spec=AsyncSession)
    repository = AsyncMock(spec=UserRepository)
    user = User(
        email="user@example.com",
        password_hash="hashed-password",
    )
    repository.get_by_email.return_value = user
    service = AuthService(session=session, repository=repository)
    request = LoginRequest(
        email="User@Example.com",
        password="existing-password",
    )

    with patch(
        "app.modules.auth.service.verify_password",
        return_value=True,
    ) as password_verifier:
        authenticated_user = await service.authenticate(request)

    assert authenticated_user is user
    repository.get_by_email.assert_awaited_once_with("user@example.com")
    password_verifier.assert_called_once_with(
        "existing-password",
        "hashed-password",
    )


@pytest.mark.anyio
async def test_authenticate_rejects_incorrect_password() -> None:
    session = AsyncMock(spec=AsyncSession)
    repository = AsyncMock(spec=UserRepository)
    repository.get_by_email.return_value = User(
        email="user@example.com",
        password_hash="hashed-password",
    )
    service = AuthService(session=session, repository=repository)
    request = LoginRequest(
        email="user@example.com",
        password="incorrect-password",
    )

    with (
        patch(
            "app.modules.auth.service.verify_password",
            return_value=False,
        ),
        pytest.raises(InvalidCredentialsError),
    ):
        await service.authenticate(request)


@pytest.mark.anyio
async def test_authenticate_uses_dummy_hash_for_missing_user() -> None:
    session = AsyncMock(spec=AsyncSession)
    repository = AsyncMock(spec=UserRepository)
    repository.get_by_email.return_value = None
    service = AuthService(session=session, repository=repository)
    request = LoginRequest(
        email="missing@example.com",
        password="existing-password",
    )

    with (
        patch(
            "app.modules.auth.service.verify_password",
            return_value=False,
        ) as password_verifier,
        pytest.raises(InvalidCredentialsError),
    ):
        await service.authenticate(request)

    password_verifier.assert_called_once()
