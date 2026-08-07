from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import jwt

from app.core.config import Settings, get_settings

_ACCESS_TOKEN_ALGORITHM = "HS256"
_TOKEN_ISSUER = "pulsewatch-api"
_TOKEN_AUDIENCE = "pulsewatch-web"


class InvalidAccessTokenError(Exception):
    pass


def create_access_token(
    user_id: UUID,
    settings: Settings | None = None,
    *,
    now: datetime | None = None,
) -> str:
    current_settings = settings or get_settings()
    issued_at = now or datetime.now(UTC)
    expires_at = issued_at + timedelta(
        minutes=current_settings.access_token_expire_minutes,
    )

    payload = {
        "sub": str(user_id),
        "type": "access",
        "iat": issued_at,
        "exp": expires_at,
        "jti": str(uuid4()),
        "iss": _TOKEN_ISSUER,
        "aud": _TOKEN_AUDIENCE,
    }

    return jwt.encode(
        payload,
        current_settings.jwt_secret_key.get_secret_value(),
        algorithm=_ACCESS_TOKEN_ALGORITHM,
    )


def decode_access_token(
    token: str,
    settings: Settings | None = None,
) -> UUID:
    current_settings = settings or get_settings()

    try:
        payload = jwt.decode(
            token,
            current_settings.jwt_secret_key.get_secret_value(),
            algorithms=[_ACCESS_TOKEN_ALGORITHM],
            issuer=_TOKEN_ISSUER,
            audience=_TOKEN_AUDIENCE,
            options={
                "require": [
                    "sub",
                    "type",
                    "iat",
                    "exp",
                    "jti",
                    "iss",
                    "aud",
                ],
            },
        )
    except jwt.InvalidTokenError as error:
        raise InvalidAccessTokenError from error

    if payload.get("type") != "access":
        raise InvalidAccessTokenError

    try:
        return UUID(payload["sub"])
    except (KeyError, TypeError, ValueError) as error:
        raise InvalidAccessTokenError from error
