from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.user import User
from app.database.session import get_database_session
from app.modules.auth.exceptions import EmailAlreadyRegisteredError
from app.modules.auth.schemas import RegisterRequest, UserResponse
from app.modules.auth.service import AuthService

router = APIRouter(prefix="/auth", tags=["authentication"])

DatabaseSession = Annotated[
    AsyncSession,
    Depends(get_database_session),
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
