from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.database import get_session
from src.repositories.absence_reason_repository import (
    AbsenceReasonRepository,
)
from src.repositories.player_repository import PlayerRepository
from src.repositories.team_repository import TeamRepository
from src.repositories.training_repository import (
    TrainingRepository,
)
from src.repositories.user_repository import UserRepository
from src.schemas.user import UserRead
from src.services import NotFoundError
from src.services.absence_reason_service import (
    AbsenceReasonService,
)
from src.services.player_service import PlayerService
from src.services.team_service import TeamService
from src.services.training_service import TrainingService
from src.services.user_service import UserService


def get_user_service(
    session: AsyncSession = Depends(get_session),
) -> UserService:
    return UserService(
        UserRepository(session)
    )


def get_player_service(
    session: AsyncSession = Depends(get_session),
) -> PlayerService:
    return PlayerService(
        PlayerRepository(session)
    )


def get_team_service(
    session: AsyncSession = Depends(get_session),
) -> TeamService:
    return TeamService(
        TeamRepository(session),
        PlayerRepository(session),
    )


def get_training_service(
    session: AsyncSession = Depends(get_session),
) -> TrainingService:
    return TrainingService(
        TrainingRepository(session),
        TeamRepository(session),
        PlayerRepository(session),
        AbsenceReasonRepository(session),
    )


def get_absence_reason_service(
    session: AsyncSession = Depends(get_session),
) -> AbsenceReasonService:
    return AbsenceReasonService(
        AbsenceReasonRepository(session)
    )


async def get_current_user(
    request: Request,
    service: UserService = Depends(
        get_user_service
    ),
) -> UserRead:
    """Только user_id хранится в cookie-сессии."""

    user_id = request.session.get(
        "user_id"
    )

    if not isinstance(user_id, int):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Требуется авторизация.",
        )

    try:
        return await service.get_by_id(
            user_id
        )

    except NotFoundError as exc:
        request.session.clear()

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
        ) from exc
