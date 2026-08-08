from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.modules.auth.exceptions import InvalidRefreshTokenError
from app.modules.auth.refresh_token_repository import (
    RefreshTokenRepository,
)
from app.security.refresh_tokens import (
    generate_refresh_token,
    hash_refresh_token,
)


@dataclass(frozen=True, slots=True)
class RefreshTokenRotation:
    user_id: UUID
    token: str


class RefreshTokenService:
    def __init__(
        self,
        session: AsyncSession,
        settings: Settings | None = None,
        repository: RefreshTokenRepository | None = None,
    ) -> None:
        self.session = session
        self.settings = settings or get_settings()
        self.repository = repository or RefreshTokenRepository(session)

    async def issue(
        self,
        user_id: UUID,
        *,
        now: datetime | None = None,
    ) -> str:
        issued_at = now or datetime.now(UTC)
        raw_token = generate_refresh_token()

        await self.repository.create(
            user_id=user_id,
            token_hash=hash_refresh_token(raw_token),
            expires_at=issued_at
            + timedelta(days=self.settings.refresh_token_expire_days),
        )
        await self.session.commit()

        return raw_token

    async def rotate(
        self,
        raw_token: str,
        *,
        now: datetime | None = None,
    ) -> RefreshTokenRotation:
        rotated_at = now or datetime.now(UTC)
        stored_token = await self.repository.get_active_by_hash(
            hash_refresh_token(raw_token),
        )

        if stored_token is None:
            raise InvalidRefreshTokenError

        self.repository.revoke(
            stored_token,
            revoked_at=rotated_at,
        )

        new_raw_token = generate_refresh_token()
        await self.repository.create(
            user_id=stored_token.user_id,
            token_hash=hash_refresh_token(new_raw_token),
            expires_at=rotated_at
            + timedelta(days=self.settings.refresh_token_expire_days),
        )
        await self.session.commit()

        return RefreshTokenRotation(
            user_id=stored_token.user_id,
            token=new_raw_token,
        )

    async def revoke(
        self,
        raw_token: str,
        *,
        now: datetime | None = None,
    ) -> bool:
        revoked_at = now or datetime.now(UTC)
        stored_token = await self.repository.get_active_by_hash(
            hash_refresh_token(raw_token),
        )

        if stored_token is None:
            return False

        self.repository.revoke(
            stored_token,
            revoked_at=revoked_at,
        )
        await self.session.commit()

        return True
