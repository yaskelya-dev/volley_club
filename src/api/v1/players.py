from fastapi import APIRouter, Depends, HTTPException, status

from src.core.dependencies import get_current_user, get_player_service
from src.schemas.player import PlayerCreate, PlayerRead, PlayerUpdate
from src.schemas.user import UserRead
from src.services import NotFoundError, ValidationServiceError
from src.services.player_service import PlayerService


router = APIRouter(
    prefix="/players",
    tags=["players"],
)


@router.get(
    "",
    response_model=list[PlayerRead],
)
async def list_players(
    current_user: UserRead = Depends(get_current_user),
    service: PlayerService = Depends(get_player_service),
) -> list[PlayerRead]:
    return await service.list(current_user.id)


@router.get(
    "/{player_id}",
    response_model=PlayerRead,
)
async def get_player(
    player_id: int,
    current_user: UserRead = Depends(get_current_user),
    service: PlayerService = Depends(get_player_service),
) -> PlayerRead:
    try:
        return await service.get(
            current_user.id,
            player_id,
        )
    except NotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc


@router.post(
    "",
    response_model=PlayerRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_player(
    payload: PlayerCreate,
    current_user: UserRead = Depends(get_current_user),
    service: PlayerService = Depends(get_player_service),
) -> PlayerRead:
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
    "/{player_id}",
    response_model=PlayerRead,
)
async def update_player(
    player_id: int,
    payload: PlayerUpdate,
    current_user: UserRead = Depends(get_current_user),
    service: PlayerService = Depends(get_player_service),
) -> PlayerRead:
    try:
        return await service.update(
            current_user.id,
            player_id,
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
    "/{player_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_player(
    player_id: int,
    current_user: UserRead = Depends(get_current_user),
    service: PlayerService = Depends(get_player_service),
) -> None:
    try:
        await service.delete(
            current_user.id,
            player_id,
        )
    except NotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc
