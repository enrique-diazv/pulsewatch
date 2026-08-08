from typing import Annotated

from fastapi import APIRouter, Cookie, Depends, HTTPException, Response, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.database.models.user import User
from app.database.session import get_database_session
from app.modules.auth.cookies import (
    REFRESH_TOKEN_COOKIE_NAME,
    clear_refresh_token_cookie,
    set_refresh_token_cookie,
)
from app.modules.auth.dependencies import get_current_user
from app.modules.auth.exceptions import (
    EmailAlreadyRegisteredError,
    InvalidCredentialsError,
    InvalidRefreshTokenError,
)
from app.modules.auth.refresh_token_service import RefreshTokenService
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
RefreshTokenCookie = Annotated[
    str | None,
    Cookie(alias=REFRESH_TOKEN_COOKIE_NAME),
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
    response: Response,
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
    access_token = create_access_token(user.id)
    refresh_token = await RefreshTokenService(
        session=session,
        settings=settings,
    ).issue(user.id)

    set_refresh_token_cookie(
        response,
        refresh_token,
        settings,
    )

    return AccessTokenResponse(
        access_token=access_token,
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


def create_invalid_refresh_response(
    settings: Settings,
) -> JSONResponse:
    response = JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content={
            "detail": "Invalid or expired refresh token",
        },
    )
    clear_refresh_token_cookie(response, settings)

    return response


@router.post(
    "/refresh",
    response_model=AccessTokenResponse,
    summary="Refresh access token",
)
async def refresh_access_token(
    response: Response,
    session: DatabaseSession,
    refresh_token: RefreshTokenCookie = None,
) -> AccessTokenResponse | Response:
    settings = get_settings()

    if refresh_token is None:
        return create_invalid_refresh_response(settings)

    try:
        rotation = await RefreshTokenService(
            session=session,
            settings=settings,
        ).rotate(refresh_token)
    except InvalidRefreshTokenError:
        return create_invalid_refresh_response(settings)

    set_refresh_token_cookie(
        response,
        rotation.token,
        settings,
    )

    return AccessTokenResponse(
        access_token=create_access_token(rotation.user_id),
        expires_in=settings.access_token_expire_minutes * 60,
    )


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Log out",
)
async def logout_user(
    response: Response,
    session: DatabaseSession,
    refresh_token: RefreshTokenCookie = None,
) -> Response:
    settings = get_settings()

    if refresh_token is not None:
        await RefreshTokenService(
            session=session,
            settings=settings,
        ).revoke(refresh_token)

    clear_refresh_token_cookie(response, settings)
    response.status_code = status.HTTP_204_NO_CONTENT

    return response
