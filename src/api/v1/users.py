from fastapi import APIRouter, Depends, HTTPException, Request, status

from src.core.dependencies import get_current_user, get_user_service
from src.schemas.user import UserLogin, UserRead, UserRegister
from src.services import (
    AlreadyExistsError,
    InvalidCredentialsError,
    ValidationServiceError,
)
from src.services.user_service import UserService


router = APIRouter(
    prefix="/users",
    tags=["users"],
)


@router.post(
    "/register",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
)
async def register(
    payload: UserRegister,
    request: Request,
    service: UserService = Depends(get_user_service),
) -> UserRead:
    try:
        user = await service.register(
            payload.name,
            payload.password,
        )

        # После регистрации сразу создаём обычную cookie-сессию — JWT здесь не используется.
        request.session.clear()
        request.session["user_id"] = user.id

        return user

    except AlreadyExistsError as exc:
        raise HTTPException(
            status_code=409,
            detail=str(exc),
        ) from exc

    except ValidationServiceError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc


@router.post(
    "/login",
    response_model=UserRead,
)
async def login(
    payload: UserLogin,
    request: Request,
    service: UserService = Depends(get_user_service),
) -> UserRead:
    try:
        user = await service.login(
            payload.name,
            payload.password,
        )

        request.session.clear()
        request.session["user_id"] = user.id

        return user

    except InvalidCredentialsError as exc:
        raise HTTPException(
            status_code=401,
            detail=str(exc),
        ) from exc

    except ValidationServiceError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc


@router.get(
    "/me",
    response_model=UserRead,
)
async def me(
    current_user: UserRead = Depends(get_current_user),
) -> UserRead:
    return current_user
