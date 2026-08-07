from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.user import User
from app.modules.auth.exceptions import (
    EmailAlreadyRegisteredError,
    InvalidCredentialsError,
)
from app.modules.auth.repository import UserRepository
from app.modules.auth.schemas import LoginRequest, RegisterRequest
from app.security.passwords import hash_password, verify_password

_DUMMY_PASSWORD_HASH = hash_password(
    "pulsewatch-login-timing-placeholder",
)


class AuthService:
    def __init__(
        self,
        session: AsyncSession,
        repository: UserRepository | None = None,
    ) -> None:
        self.session = session
        self.repository = repository or UserRepository(session)

    async def register(self, request: RegisterRequest) -> User:
        normalized_email = str(request.email).casefold()
        existing_user = await self.repository.get_by_email(normalized_email)

        if existing_user is not None:
            raise EmailAlreadyRegisteredError

        try:
            user = await self.repository.create(
                email=normalized_email,
                password_hash=hash_password(request.password),
            )
            await self.session.commit()
        except IntegrityError as error:
            await self.session.rollback()
            raise EmailAlreadyRegisteredError from error

        await self.session.refresh(user)

        return user

    async def authenticate(self, request: LoginRequest) -> User:
        normalized_email = str(request.email).casefold()
        user = await self.repository.get_by_email(normalized_email)

        candidate_hash = (
            user.password_hash if user is not None else _DUMMY_PASSWORD_HASH
        )
        password_is_valid = verify_password(
            request.password,
            candidate_hash,
        )

        if user is None or not password_is_valid:
            raise InvalidCredentialsError

        return user
