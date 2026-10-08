from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)

from src.core.dependencies import (
    get_absence_reason_service,
    get_current_user,
)
from src.schemas.absence_reason import (
    AbsenceReasonCreate,
    AbsenceReasonRead,
    AbsenceReasonUpdate,
)
from src.schemas.user import UserRead
from src.services import (
    NotFoundError,
    ValidationServiceError,
)
from src.services.absence_reason_service import (
    AbsenceReasonService,
)


router = APIRouter(
    prefix="/absence-reasons",
    tags=["absence-reasons"],
)


@router.get(
    "",
    response_model=list[AbsenceReasonRead],
)
async def list_absence_reasons(
    current_user: UserRead = Depends(
        get_current_user
    ),
    service: AbsenceReasonService = Depends(
        get_absence_reason_service
    ),
) -> list[AbsenceReasonRead]:
    return await service.list(
        current_user.id
    )


@router.get(
    "/{reason_id}",
    response_model=AbsenceReasonRead,
)
async def get_absence_reason(
    reason_id: int,
    current_user: UserRead = Depends(
        get_current_user
    ),
    service: AbsenceReasonService = Depends(
        get_absence_reason_service
    ),
) -> AbsenceReasonRead:
    try:
        return await service.get(
            current_user.id,
            reason_id,
        )

    except NotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc


@router.post(
    "",
    response_model=AbsenceReasonRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_absence_reason(
    payload: AbsenceReasonCreate,
    current_user: UserRead = Depends(
        get_current_user
    ),
    service: AbsenceReasonService = Depends(
        get_absence_reason_service
    ),
) -> AbsenceReasonRead:
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
    "/{reason_id}",
    response_model=AbsenceReasonRead,
)
async def update_absence_reason(
    reason_id: int,
    payload: AbsenceReasonUpdate,
    current_user: UserRead = Depends(
        get_current_user
    ),
    service: AbsenceReasonService = Depends(
        get_absence_reason_service
    ),
) -> AbsenceReasonRead:
    try:
        return await service.update(
            current_user.id,
            reason_id,
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
    "/{reason_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_absence_reason(
    reason_id: int,
    current_user: UserRead = Depends(
        get_current_user
    ),
    service: AbsenceReasonService = Depends(
        get_absence_reason_service
    ),
) -> None:
    try:
        await service.delete(
            current_user.id,
            reason_id,
        )

    except NotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc
