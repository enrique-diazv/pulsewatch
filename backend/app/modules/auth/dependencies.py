from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.user import User
from app.database.session import get_database_session
from app.modules.auth.repository import UserRepository
from app.security.tokens import (
    InvalidAccessTokenError,
    decode_access_token,
)

bearer_scheme = HTTPBearer(auto_error=False)

DatabaseSession = Annotated[
    AsyncSession,
    Depends(get_database_session),
]

BearerCredentials = Annotated[
    HTTPAuthorizationCredentials | None,
    Depends(bearer_scheme),
]


def create_unauthorized_error() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or missing access token",
        headers={"WWW-Authenticate": "Bearer"},
    )


async def get_current_user(
    credentials: BearerCredentials,
    session: DatabaseSession,
) -> User:
    if credentials is None:
        raise create_unauthorized_error()

    try:
        user_id = decode_access_token(credentials.credentials)
    except InvalidAccessTokenError as error:
        raise create_unauthorized_error() from error

    user = await UserRepository(session).get_by_id(user_id)

    if user is None:
        raise create_unauthorized_error()

    return user
