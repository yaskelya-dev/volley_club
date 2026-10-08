from fastapi import APIRouter, Depends, HTTPException, status

from src.core.dependencies import get_current_user, get_team_service
from src.schemas.team import TeamCreate, TeamDetail, TeamRead, TeamUpdate
from src.schemas.user import UserRead
from src.services import (
    AlreadyExistsError,
    NotFoundError,
    ValidationServiceError,
)
from src.services.team_service import TeamService


router = APIRouter(
    prefix="/teams",
    tags=["teams"],
)


@router.get(
    "",
    response_model=list[TeamDetail],
)
async def list_teams(
    current_user: UserRead = Depends(get_current_user),
    service: TeamService = Depends(get_team_service),
) -> list[TeamDetail]:
    return await service.list(current_user.id)


@router.get(
    "/{team_id}",
    response_model=TeamDetail,
)
async def get_team(
    team_id: int,
    current_user: UserRead = Depends(get_current_user),
    service: TeamService = Depends(get_team_service),
) -> TeamDetail:
    try:
        return await service.get(
            current_user.id,
            team_id,
        )
    except NotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc


@router.post(
    "",
    response_model=TeamRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_team(
    payload: TeamCreate,
    current_user: UserRead = Depends(get_current_user),
    service: TeamService = Depends(get_team_service),
) -> TeamRead:
    try:
        return await service.create(
            current_user.id,
            payload,
        )
    except ValidationServiceError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc


@router.put(
    "/{team_id}",
    response_model=TeamRead,
)
async def update_team(
    team_id: int,
    payload: TeamUpdate,
    current_user: UserRead = Depends(get_current_user),
    service: TeamService = Depends(get_team_service),
) -> TeamRead:
    try:
        return await service.update(
            current_user.id,
            team_id,
            payload,
        )
    except NotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc
    except ValidationServiceError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc


@router.delete(
    "/{team_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_team(
    team_id: int,
    current_user: UserRead = Depends(get_current_user),
    service: TeamService = Depends(get_team_service),
) -> None:
    try:
        await service.delete(
            current_user.id,
            team_id,
        )
    except NotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc


@router.post(
    "/{team_id}/players/{player_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def add_player_to_team(
    team_id: int,
    player_id: int,
    current_user: UserRead = Depends(get_current_user),
    service: TeamService = Depends(get_team_service),
) -> None:
    try:
        await service.add_player(
            current_user.id,
            team_id,
            player_id,
        )
    except AlreadyExistsError as exc:
        raise HTTPException(
            status_code=409,
            detail=str(exc),
        ) from exc
    except NotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc


@router.delete(
    "/{team_id}/players/{player_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def remove_player_from_team(
    team_id: int,
    player_id: int,
    current_user: UserRead = Depends(get_current_user),
    service: TeamService = Depends(get_team_service),
) -> None:
    try:
        await service.remove_player(
            current_user.id,
            team_id,
            player_id,
        )
    except NotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc
