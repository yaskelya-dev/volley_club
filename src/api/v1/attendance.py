from fastapi import APIRouter, Depends, HTTPException

from src.core.dependencies import (
    get_current_user,
    get_training_service,
)
from src.schemas.training import (
    AttendanceItemRead,
    AttendanceUpsert,
)
from src.schemas.user import UserRead
from src.services import (
    NotFoundError,
    ValidationServiceError,
)
from src.services.training_service import TrainingService


router = APIRouter(
    tags=["attendance"]
)


@router.post(
    "/attendance",
    response_model=AttendanceItemRead,
)
async def upsert_attendance(
    payload: AttendanceUpsert,
    current_user: UserRead = Depends(
        get_current_user
    ),
    service: TrainingService = Depends(
        get_training_service
    ),
) -> AttendanceItemRead:
    try:
        return await service.upsert_attendance(
            current_user.id,
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
