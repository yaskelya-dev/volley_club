from datetime import date

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.models.base import (
    Team,
    Training,
    TrainingAttendance,
)


class TrainingRepositoryProtocol:
    async def list_by_team(
        self,
        team_id: int,
    ) -> list[Training]:
        ...

    async def get_by_id(
        self,
        training_id: int,
    ) -> Training | None:
        ...

    async def get_owned(
        self,
        training_id: int,
        user_id: int,
    ) -> Training | None:
        ...

    async def create(
        self,
        training_date: date,
        team_id: int,
    ) -> Training:
        ...

    async def update(
        self,
        training: Training,
        training_date: date,
    ) -> Training:
        ...

    async def delete(
        self,
        training: Training,
    ) -> None:
        ...

    async def attendance_map(
        self,
        training_ids: list[int],
    ) -> dict[
        tuple[int, int],
        bool,
    ]:
        ...

    async def attendance_details_map(
        self,
        training_ids: list[int],
    ) -> dict[
        tuple[int, int],
        TrainingAttendance,
    ]:
        ...

    async def attendance_map_for_training(
        self,
        training_id: int,
    ) -> dict[int, bool]:
        ...

    async def upsert_attendance(
        self,
        training_id: int,
        player_id: int,
        present: bool,
        reason_id: int | None = None,
    ) -> TrainingAttendance:
        ...

    async def clear_attendance(
        self,
        training_id: int,
        player_id: int,
    ) -> None:
        ...


class TrainingRepository(
    TrainingRepositoryProtocol
):
    def __init__(
        self,
        session: AsyncSession,
    ) -> None:
        self._session = session

    async def list_by_team(
        self,
        team_id: int,
    ) -> list[Training]:
        result = await self._session.execute(
            select(Training)
            .where(
                Training.team_id == team_id
            )
            .order_by(
                Training.date,
                Training.id,
            )
        )

        return list(
            result.scalars().all()
        )

    async def get_by_id(
        self,
        training_id: int,
    ) -> Training | None:
        return await self._session.get(
            Training,
            training_id,
        )

    async def get_owned(
        self,
        training_id: int,
        user_id: int,
    ) -> Training | None:
        result = await self._session.execute(
            select(Training)
            .join(
                Team,
                Team.id == Training.team_id,
            )
            .where(
                Training.id == training_id,
                Team.created_by == user_id,
            )
        )

        return result.scalar_one_or_none()

    async def create(
        self,
        training_date: date,
        team_id: int,
    ) -> Training:
        training = Training(
            date=training_date,
            team_id=team_id,
        )

        self._session.add(training)

        await self._session.commit()
        await self._session.refresh(training)

        return training

    async def update(
        self,
        training: Training,
        training_date: date,
    ) -> Training:
        training.date = training_date

        await self._session.commit()
        await self._session.refresh(training)

        return training

    async def delete(
        self,
        training: Training,
    ) -> None:
        await self._session.delete(training)
        await self._session.commit()

    async def attendance_map(
        self,
        training_ids: list[int],
    ) -> dict[
        tuple[int, int],
        bool,
    ]:
        if not training_ids:
            return {}

        result = await self._session.execute(
            select(TrainingAttendance)
            .where(
                TrainingAttendance.training_id.in_(
                    training_ids
                )
            )
        )

        return {
            (
                item.training_id,
                item.player_id,
            ): item.present
            for item in result.scalars().all()
        }

    async def attendance_details_map(
        self,
        training_ids: list[int],
    ) -> dict[
        tuple[int, int],
        TrainingAttendance,
    ]:
        if not training_ids:
            return {}

        result = await self._session.execute(
            select(TrainingAttendance)
            .where(
                TrainingAttendance.training_id.in_(
                    training_ids
                )
            )
            .options(
                selectinload(
                    TrainingAttendance.reason
                )
            )
        )

        return {
            (
                item.training_id,
                item.player_id,
            ): item
            for item in result.scalars().all()
        }

    async def attendance_map_for_training(
        self,
        training_id: int,
    ) -> dict[int, bool]:
        result = await self._session.execute(
            select(TrainingAttendance).where(
                TrainingAttendance.training_id
                == training_id
            )
        )

        return {
            item.player_id: item.present
            for item in result.scalars().all()
        }

    async def upsert_attendance(
        self,
        training_id: int,
        player_id: int,
        present: bool,
        reason_id: int | None = None,
    ) -> TrainingAttendance:
        item = await self._session.get(
            TrainingAttendance,
            {
                "training_id": training_id,
                "player_id": player_id,
            },
        )

        if item is None:
            item = TrainingAttendance(
                training_id=training_id,
                player_id=player_id,
                present=present,
                reason_id=reason_id,
            )

            self._session.add(item)

        else:
            item.present = present
            item.reason_id = reason_id

        await self._session.commit()
        await self._session.refresh(item)

        return item

    async def clear_attendance(
        self,
        training_id: int,
        player_id: int,
    ) -> None:
        await self._session.execute(
            delete(
                TrainingAttendance
            ).where(
                TrainingAttendance.training_id
                == training_id,
                TrainingAttendance.player_id
                == player_id,
            )
        )

        await self._session.commit()
