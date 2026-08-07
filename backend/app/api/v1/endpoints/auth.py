from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.database.models.user import User
from app.database.session import get_database_session
from app.modules.auth.dependencies import get_current_user
from app.modules.auth.exceptions import (
    EmailAlreadyRegisteredError,
    InvalidCredentialsError,
)
from app.modules.auth.schemas import (
    AccessTokenResponse,
    LoginRequest,
    RegisterRequest,
    UserResponse,
)
from app.modules.auth.service import AuthService
from app.security.tokens import create_access_token

router = APIRouter(prefix="/auth", tags=["authentication"])

DatabaseSession = Annotated[
    AsyncSession,
    Depends(get_database_session),
]
CurrentUser = Annotated[
    User,
    Depends(get_current_user),
]


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a user",
)
async def register_user(
    request: RegisterRequest,
    session: DatabaseSession,
) -> User:
    service = AuthService(session)

    try:
        return await service.register(request)
    except EmailAlreadyRegisteredError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error),
        ) from error


@router.post(
    "/login",
    response_model=AccessTokenResponse,
    summary="Log in",
)
async def login_user(
    request: LoginRequest,
    session: DatabaseSession,
) -> AccessTokenResponse:
    service = AuthService(session)

    try:
        user = await service.authenticate(request)
    except InvalidCredentialsError as error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(error),
            headers={"WWW-Authenticate": "Bearer"},
        ) from error

    settings = get_settings()

    return AccessTokenResponse(
        access_token=create_access_token(user.id),
        expires_in=settings.access_token_expire_minutes * 60,
    )


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user",
)
async def read_current_user(
    current_user: CurrentUser,
) -> User:
    return current_user
