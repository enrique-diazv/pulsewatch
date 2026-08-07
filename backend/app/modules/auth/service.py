from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.user import User
from app.modules.auth.exceptions import EmailAlreadyRegisteredError
from app.modules.auth.repository import UserRepository
from app.modules.auth.schemas import RegisterRequest
from app.security.passwords import hash_password


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
