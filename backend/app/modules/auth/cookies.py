from fastapi import Response

from app.core.config import Settings

REFRESH_TOKEN_COOKIE_NAME = "pulsewatch_refresh_token"
REFRESH_TOKEN_COOKIE_PATH = "/api/v1/auth"


def set_refresh_token_cookie(
    response: Response,
    token: str,
    settings: Settings,
) -> None:
    response.set_cookie(
        key=REFRESH_TOKEN_COOKIE_NAME,
        value=token,
        max_age=settings.refresh_token_expire_days * 24 * 60 * 60,
        path=REFRESH_TOKEN_COOKIE_PATH,
        secure=settings.environment == "production",
        httponly=True,
        samesite="lax",
    )


def clear_refresh_token_cookie(
    response: Response,
    settings: Settings,
) -> None:
    response.delete_cookie(
        key=REFRESH_TOKEN_COOKIE_NAME,
        path=REFRESH_TOKEN_COOKIE_PATH,
        secure=settings.environment == "production",
        httponly=True,
        samesite="lax",
    )
