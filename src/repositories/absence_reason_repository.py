from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.base import AbsenceReason


class AbsenceReasonRepositoryProtocol:
    async def list_by_owner(
        self,
        user_id: int,
    ) -> list[AbsenceReason]:
        ...

    async def get_owned(
        self,
        reason_id: int,
        user_id: int,
    ) -> AbsenceReason | None:
        ...

    async def create(
        self,
        name: str,
        user_id: int,
        is_valid: bool,
    ) -> AbsenceReason:
        ...

    async def update(
        self,
        reason: AbsenceReason,
        name: str,
        is_valid: bool,
    ) -> AbsenceReason:
        ...

    async def delete(
        self,
        reason: AbsenceReason,
    ) -> None:
        ...


class AbsenceReasonRepository(
    AbsenceReasonRepositoryProtocol
):
    def __init__(
        self,
        session: AsyncSession,
    ) -> None:
        self._session = session

    async def list_by_owner(
        self,
        user_id: int,
    ) -> list[AbsenceReason]:
        result = await self._session.execute(
            select(AbsenceReason)
            .where(
                AbsenceReason.created_by == user_id
            )
            .order_by(
                AbsenceReason.name
            )
        )

        return list(
            result.scalars().all()
        )

    async def get_owned(
        self,
        reason_id: int,
        user_id: int,
    ) -> AbsenceReason | None:
        result = await self._session.execute(
            select(AbsenceReason).where(
                AbsenceReason.id == reason_id,
                AbsenceReason.created_by == user_id,
            )
        )

        return result.scalar_one_or_none()

    async def create(
        self,
        name: str,
        user_id: int,
        is_valid: bool,
    ) -> AbsenceReason:
        reason = AbsenceReason(
            name=name,
            created_by=user_id,
            is_valid=is_valid,
        )

        self._session.add(reason)

        await self._session.commit()
        await self._session.refresh(reason)

        return reason

    async def update(
        self,
        reason: AbsenceReason,
        name: str,
        is_valid: bool,
    ) -> AbsenceReason:
        reason.name = name
        reason.is_valid = is_valid

        await self._session.commit()
        await self._session.refresh(reason)

        return reason

    async def delete(
        self,
        reason: AbsenceReason,
    ) -> None:
        await self._session.delete(reason)
        await self._session.commit()
