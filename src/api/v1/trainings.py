from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    status,
)

from src.core.dependencies import (
    get_current_user,
    get_training_service,
)
from src.schemas.training import (
    AttendanceUpdate,
    TrainingCreate,
    TrainingMatrixResponse,
    TrainingRead,
    TrainingUpdate,
)
from src.schemas.user import UserRead
from src.services import (
    NotFoundError,
    ValidationServiceError,
)
from src.services.training_service import (
    TrainingService,
)


router = APIRouter(
    prefix="/trainings",
    tags=["trainings"],
)


@router.get(
    "/team/{team_id}",
    response_model=list[TrainingRead],
)
async def list_trainings(
    team_id: int,
    current_user: UserRead = Depends(
        get_current_user
    ),
    service: TrainingService = Depends(
        get_training_service
    ),
) -> list[TrainingRead]:
    try:
        return await service.list_for_team(
            current_user.id,
            team_id,
        )

    except NotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc


@router.get(
    "/team/{team_id}/matrix",
    response_model=TrainingMatrixResponse,
)
async def training_page_data(
    team_id: int,
    selected_training_id: int | None = Query(
        default=None,
        gt=0,
    ),
    current_user: UserRead = Depends(
        get_current_user
    ),
    service: TrainingService = Depends(
        get_training_service
    ),
) -> TrainingMatrixResponse:
    try:
        return await service.build_matrix(
            current_user.id,
            team_id,
            selected_training_id,
        )

    except NotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc


@router.get(
    "/{training_id}",
    response_model=TrainingRead,
)
async def get_training(
    training_id: int,
    current_user: UserRead = Depends(
        get_current_user
    ),
    service: TrainingService = Depends(
        get_training_service
    ),
) -> TrainingRead:
    try:
        return await service.get(
            current_user.id,
            training_id,
        )

    except NotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc


@router.post(
    "",
    response_model=TrainingRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_training(
    payload: TrainingCreate,
    current_user: UserRead = Depends(
        get_current_user
    ),
    service: TrainingService = Depends(
        get_training_service
    ),
) -> TrainingRead:
    try:
        return await service.create(
            current_user.id,
            payload,
        )

    except NotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc


@router.put(
    "/{training_id}",
    response_model=TrainingRead,
)
async def update_training(
    training_id: int,
    payload: TrainingUpdate,
    current_user: UserRead = Depends(
        get_current_user
    ),
    service: TrainingService = Depends(
        get_training_service
    ),
) -> TrainingRead:
    try:
        return await service.update(
            current_user.id,
            training_id,
            payload,
        )

    except NotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc


@router.delete(
    "/{training_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_training(
    training_id: int,
    current_user: UserRead = Depends(
        get_current_user
    ),
    service: TrainingService = Depends(
        get_training_service
    ),
) -> None:
    try:
        await service.delete(
            current_user.id,
            training_id,
        )

    except NotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc


@router.put(
    "/{training_id}/attendance",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def set_attendance(
    training_id: int,
    payload: AttendanceUpdate,
    current_user: UserRead = Depends(
        get_current_user
    ),
    service: TrainingService = Depends(
        get_training_service
    ),
) -> None:
    """
    Старый API-контракт не изменён.
    """

    try:
        await service.set_attendance(
            current_user.id,
            training_id,
            payload.player_id,
            payload.present,
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
