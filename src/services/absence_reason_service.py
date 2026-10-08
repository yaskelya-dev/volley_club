from src.repositories.absence_reason_repository import (
    AbsenceReasonRepositoryProtocol,
)
from src.schemas.absence_reason import (
    AbsenceReasonCreate,
    AbsenceReasonRead,
    AbsenceReasonUpdate,
)
from src.services import (
    NotFoundError,
    ValidationServiceError,
)


class AbsenceReasonService:
    def __init__(
        self,
        repository: AbsenceReasonRepositoryProtocol,
    ) -> None:
        self._repository = repository

    async def list(
        self,
        user_id: int,
    ) -> list[AbsenceReasonRead]:
        return [
            AbsenceReasonRead.model_validate(item)
            for item
            in await self._repository.list_by_owner(
                user_id
            )
        ]

    async def get(
        self,
        user_id: int,
        reason_id: int,
    ) -> AbsenceReasonRead:
        reason = await self._repository.get_owned(
            reason_id,
            user_id,
        )

        if reason is None:
            raise NotFoundError(
                "Причина не найдена."
            )

        return AbsenceReasonRead.model_validate(
            reason
        )

    async def create(
        self,
        user_id: int,
        payload: AbsenceReasonCreate,
    ) -> AbsenceReasonRead:
        name = payload.name.strip()

        if not name:
            raise ValidationServiceError(
                "Причина не может быть пустой."
            )

        reason = await self._repository.create(
            name,
            user_id,
            payload.is_valid,
        )

        return AbsenceReasonRead.model_validate(
            reason
        )

    async def update(
        self,
        user_id: int,
        reason_id: int,
        payload: AbsenceReasonUpdate,
    ) -> AbsenceReasonRead:
        reason = await self._repository.get_owned(
            reason_id,
            user_id,
        )

        if reason is None:
            raise NotFoundError(
                "Причина не найдена."
            )

        name = payload.name.strip()

        if not name:
            raise ValidationServiceError(
                "Причина не может быть пустой."
            )

        reason = await self._repository.update(
            reason,
            name,
            payload.is_valid,
        )

        return AbsenceReasonRead.model_validate(
            reason
        )

    async def delete(
        self,
        user_id: int,
        reason_id: int,
    ) -> None:
        reason = await self._repository.get_owned(
            reason_id,
            user_id,
        )

        if reason is None:
            raise NotFoundError(
                "Причина не найдена."
            )

        await self._repository.delete(reason)
