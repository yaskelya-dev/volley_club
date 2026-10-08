from datetime import date

from pydantic import BaseModel

from src.repositories.absence_reason_repository import (
    AbsenceReasonRepositoryProtocol,
)
from src.repositories.player_repository import (
    PlayerRepositoryProtocol,
)
from src.repositories.team_repository import (
    TeamRepositoryProtocol,
)
from src.repositories.training_repository import (
    TrainingRepositoryProtocol,
)
from src.schemas.absence_reason import (
    AbsenceReasonRead,
)
from src.schemas.player import PlayerRead
from src.schemas.training import (
    AttendanceItemRead,
    AttendanceMarkDTO,
    AttendanceRead,
    AttendanceUpsert,
    AttendanceViewDTO,
    AttendanceViewRowDTO,
    AttendanceViewTrainingDTO,
    TrainingCreate,
    TrainingMatrixResponse,
    TrainingMatrixRow,
    TrainingRead,
    TrainingUpdate,
)
from src.services import (
    NotFoundError,
    ValidationServiceError,
)


class TrainingService:
    def __init__(
        self,
        repository: TrainingRepositoryProtocol,
        team_repository: TeamRepositoryProtocol,
        player_repository: PlayerRepositoryProtocol,
        absence_reason_repository: (
            AbsenceReasonRepositoryProtocol
        ),
    ) -> None:
        self._repository = repository
        self._team_repository = team_repository
        self._player_repository = player_repository
        self._absence_reason_repository = (
            absence_reason_repository
        )

    async def list_for_team(
        self,
        user_id: int,
        team_id: int,
    ) -> list[TrainingRead]:
        team = await self._team_repository.get_owned(
            team_id,
            user_id,
        )

        if team is None:
            raise NotFoundError(
                "Команда не найдена."
            )

        trainings = (
            await self._repository.list_by_team(
                team_id
            )
        )

        return [
            TrainingRead.model_validate(
                item
            )
            for item in trainings
        ]

    async def get(
        self,
        user_id: int,
        training_id: int,
    ) -> TrainingRead:
        training = (
            await self._repository.get_owned(
                training_id,
                user_id,
            )
        )

        if training is None:
            raise NotFoundError(
                "Тренировка не найдена."
            )

        return TrainingRead.model_validate(
            training
        )

    async def create(
        self,
        user_id: int,
        payload: TrainingCreate,
    ) -> TrainingRead:
        team = await self._team_repository.get_owned(
            payload.team_id,
            user_id,
        )

        if team is None:
            raise NotFoundError(
                "Команда не найдена."
            )

        training = await self._repository.create(
            payload.date,
            payload.team_id,
        )

        return TrainingRead.model_validate(
            training
        )

    async def update(
        self,
        user_id: int,
        training_id: int,
        payload: TrainingUpdate,
    ) -> TrainingRead:
        training = (
            await self._repository.get_owned(
                training_id,
                user_id,
            )
        )

        if training is None:
            raise NotFoundError(
                "Тренировка не найдена."
            )

        training = await self._repository.update(
            training,
            payload.date,
        )

        return TrainingRead.model_validate(
            training
        )

    async def delete(
        self,
        user_id: int,
        training_id: int,
    ) -> None:
        training = (
            await self._repository.get_owned(
                training_id,
                user_id,
            )
        )

        if training is None:
            raise NotFoundError(
                "Тренировка не найдена."
            )

        await self._repository.delete(
            training
        )

    async def set_attendance(
        self,
        user_id: int,
        training_id: int,
        player_id: int,
        present: bool,
    ) -> None:
        """
        Старый API-контракт.

        Он по-прежнему принимает только present и не требует
        reason_id, поэтому существующий API не ломается.
        """
        training = (
            await self._repository.get_owned(
                training_id,
                user_id,
            )
        )

        if training is None:
            raise NotFoundError(
                "Тренировка не найдена."
            )

        player = (
            await self._player_repository.get_owned(
                player_id,
                user_id,
            )
        )

        if player is None:
            raise NotFoundError(
                "Игрок не найден."
            )

        team = await self._team_repository.get_owned(
            training.team_id,
            user_id,
        )

        assert team is not None

        if not any(
            item.id == player_id
            for item in team.players
        ):
            raise ValidationServiceError(
                "Игрок не состоит в выбранной команде."
            )

        await self._repository.upsert_attendance(
            training_id,
            player_id,
            present,
            None,
        )

    async def upsert_attendance(
        self,
        user_id: int,
        payload: AttendanceUpsert,
    ) -> AttendanceItemRead:
        """
        Новый единый контракт attendance.

        absent обязательно требует reason_id.
        none полностью удаляет запись attendance.
        """
        training = (
            await self._repository.get_owned(
                payload.training_id,
                user_id,
            )
        )

        if training is None:
            raise NotFoundError(
                "Тренировка не найдена."
            )

        player = (
            await self._player_repository.get_owned(
                payload.player_id,
                user_id,
            )
        )

        if player is None:
            raise NotFoundError(
                "Игрок не найден."
            )

        team = await self._team_repository.get_owned(
            training.team_id,
            user_id,
        )

        assert team is not None

        if not any(
            item.id == payload.player_id
            for item in team.players
        ):
            raise ValidationServiceError(
                "Игрок не состоит в выбранной команде."
            )

        if payload.status == "absent":
            if payload.reason_id is None:
                raise ValidationServiceError(
                    "Для прогула необходимо указать причину."
                )

            reason = (
                await self._absence_reason_repository.get_owned(
                    payload.reason_id,
                    user_id,
                )
            )

            if reason is None:
                raise NotFoundError(
                    "Причина прогула не найдена."
                )

            attendance = (
                await self._repository.upsert_attendance(
                    payload.training_id,
                    payload.player_id,
                    False,
                    reason.id,
                )
            )

            return AttendanceItemRead(
                player_id=attendance.player_id,
                training_id=attendance.training_id,
                status="absent",
                reason_id=reason.id,
                reason_name=reason.name,
                is_valid=reason.is_valid,
            )

        if payload.status == "present":
            attendance = (
                await self._repository.upsert_attendance(
                    payload.training_id,
                    payload.player_id,
                    True,
                    None,
                )
            )

            return AttendanceItemRead(
                player_id=attendance.player_id,
                training_id=attendance.training_id,
                status="present",
                reason_id=None,
                reason_name=None,
                is_valid=False,
            )

        # none
        await self._repository.clear_attendance(
            payload.training_id,
            payload.player_id,
        )

        return AttendanceItemRead(
            player_id=payload.player_id,
            training_id=payload.training_id,
            status="none",
            reason_id=None,
            reason_name=None,
            is_valid=False,
        )

    @staticmethod
    def _select_attendance_trainings(
        trainings: list,
    ) -> list:
        """
        Главная бизнес-логика выбора максимум трёх тренировок.
        """
        if not trainings:
            return []

        today = date.today()

        past = [
            item
            for item in trainings
            if item.date <= today
        ]

        future = [
            item
            for item in trainings
            if item.date > today
        ]

        # Идеальный случай:
        # ближайшая прошедшая/сегодняшняя + два будущих.
        if past and len(future) >= 2:
            return [
                past[-1],
                future[0],
                future[1],
            ]

        # Будущих меньше двух:
        # добираем последними прошедшими.
        if past:
            selected = [
                past[-1],
                *future[:2],
            ]

            selected_ids = {
                item.id
                for item in selected
            }

            for item in reversed(
                past[:-1]
            ):
                if len(selected) >= 3:
                    break

                if item.id not in selected_ids:
                    selected.append(item)
                    selected_ids.add(item.id)

            selected.sort(
                key=lambda item: (
                    item.date,
                    item.id,
                )
            )

            return selected[:3]

        # Все тренировки пока в будущем.
        return future[:3]

    async def _build_attendance_view(
        self,
        user_id: int,
        team_id: int,
        trainings: list,
    ) -> "AttendanceViewDTO":
        team = await self._team_repository.get_owned(
            team_id,
            user_id,
        )

        if team is None:
            raise NotFoundError(
                "Команда не найдена."
            )

        players = sorted(
            team.players,
            key=lambda player: (
                player.name.casefold()
            ),
        )

        attendance = (
            await self._repository.attendance_details_map(
                [
                    item.id
                    for item in trainings
                ]
            )
        )

        rows: list[
            AttendanceViewRowDTO
        ] = []

        for row_number, player in enumerate(
            players,
            start=1,
        ):
            marks: list[
                AttendanceMarkDTO | None
            ] = []

            for training in trainings:
                item = attendance.get(
                    (
                        training.id,
                        player.id,
                    )
                )

                if item is None:
                    marks.append(None)
                    continue

                if item.present:
                    marks.append(
                        AttendanceMarkDTO(
                            status="present",
                            reason_id=None,
                            reason_name=None,
                            is_valid=False,
                        )
                    )
                    continue

                # Старые записи absent могли быть сохранены
                # без reason_id — это намеренно красный статус.
                marks.append(
                    AttendanceMarkDTO(
                        status="absent",
                        reason_id=item.reason_id,
                        reason_name=(
                            item.reason.name
                            if item.reason is not None
                            else None
                        ),
                        is_valid=(
                            item.reason.is_valid
                            if item.reason is not None
                            else False
                        ),
                    )
                )

            rows.append(
                AttendanceViewRowDTO(
                    row_number=row_number,
                    player=PlayerRead.model_validate(
                        player
                    ),
                    marks=marks,
                )
            )

        reasons = [
            AbsenceReasonRead.model_validate(
                reason
            )
            for reason
            in await self._absence_reason_repository.list_by_owner(
                user_id
            )
        ]

        return AttendanceViewDTO(
            team_id=team_id,
            trainings=[
                AttendanceViewTrainingDTO(
                    id=item.id,
                    date=item.date,
                )
                for item in trainings
            ],
            rows=rows,
            reasons=reasons,
        )

    async def get_attendance_view(
        self,
        user_id: int,
        team_id: int,
    ) -> AttendanceViewDTO:
        """
        DTO для главной /trainings.

        Здесь происходит весь выбор трёх тренировок и
        сбор данных по причинам.
        """
        team = await self._team_repository.get_owned(
            team_id,
            user_id,
        )

        if team is None:
            raise NotFoundError(
                "Команда не найдена."
            )

        all_trainings = (
            await self._repository.list_by_team(
                team_id
            )
        )

        selected_trainings = (
            self._select_attendance_trainings(
                all_trainings
            )
        )

        return await self._build_attendance_view(
            user_id,
            team_id,
            selected_trainings,
        )

    async def get_all_attendance_view(
        self,
        user_id: int,
        team_id: int,
    ) -> AttendanceViewDTO:
        """DTO для полной истории всех тренировок."""
        team = await self._team_repository.get_owned(
            team_id,
            user_id,
        )

        if team is None:
            raise NotFoundError(
                "Команда не найдена."
            )

        all_trainings = (
            await self._repository.list_by_team(
                team_id
            )
        )

        return await self._build_attendance_view(
            user_id,
            team_id,
            all_trainings,
        )

    async def build_matrix(
        self,
        user_id: int,
        team_id: int,
        selected_training_id: int | None = None,
    ) -> TrainingMatrixResponse:
        """
        Старый DTO /matrix.

        Оставлен для рабочего API и не участвует
        в новой web-странице.
        """
        team = await self._team_repository.get_owned(
            team_id,
            user_id,
        )

        if team is None:
            raise NotFoundError(
                "Команда не найдена."
            )

        trainings = (
            await self._repository.list_by_team(
                team_id
            )
        )

        players = sorted(
            team.players,
            key=lambda p: p.name.lower(),
        )

        if not trainings:
            return TrainingMatrixResponse(
                selected_training=None,
                trainings=[],
                rows=[
                    TrainingMatrixRow(
                        row_number=i,
                        player=PlayerRead.model_validate(
                            player
                        ),
                        previous=None,
                        next_1=None,
                        next_2=None,
                    )
                    for i, player
                    in enumerate(
                        players,
                        start=1,
                    )
                ],
                selected_attendance=[],
            )

        selected_index = None

        if selected_training_id is not None:
            for idx, training in enumerate(
                trainings
            ):
                if training.id == selected_training_id:
                    selected_index = idx
                    break

            if selected_index is None:
                raise NotFoundError(
                    "Выбранная тренировка "
                    "не найдена в этой команде."
                )

        else:
            passed = [
                i
                for i, item
                in enumerate(trainings)
                if item.date <= date.today()
            ]

            selected_index = (
                passed[-1]
                if passed
                else 0
            )

        selected_training = trainings[
            selected_index
        ]

        previous_id = (
            trainings[
                selected_index - 1
            ].id
            if selected_index - 1 >= 0
            else None
        )

        next1_id = (
            trainings[
                selected_index + 1
            ].id
            if selected_index + 1
            < len(trainings)
            else None
        )

        next2_id = (
            trainings[
                selected_index + 2
            ].id
            if selected_index + 2
            < len(trainings)
            else None
        )

        context_ids = [
            x
            for x in (
                previous_id,
                next1_id,
                next2_id,
            )
            if x is not None
        ]

        attendance = (
            await self._repository.attendance_map(
                context_ids
            )
        )

        selected_attendance_map = (
            await self._repository
            .attendance_map_for_training(
                selected_training.id
            )
        )

        rows: list[
            TrainingMatrixRow
        ] = []

        for row_number, player in enumerate(
            players,
            start=1,
        ):
            rows.append(
                TrainingMatrixRow(
                    row_number=row_number,
                    player=PlayerRead.model_validate(
                        player
                    ),
                    previous=(
                        attendance.get(
                            (
                                previous_id,
                                player.id,
                            )
                        )
                        if previous_id
                        else None
                    ),
                    next_1=(
                        attendance.get(
                            (
                                next1_id,
                                player.id,
                            )
                        )
                        if next1_id
                        else None
                    ),
                    next_2=(
                        attendance.get(
                            (
                                next2_id,
                                player.id,
                            )
                        )
                        if next2_id
                        else None
                    ),
                )
            )

        selected_attendance = [
            AttendanceRead(
                player_id=player.id,
                present=(
                    selected_attendance_map[
                        player.id
                    ]
                ),
            )
            for player in players
            if player.id
            in selected_attendance_map
        ]

        return TrainingMatrixResponse(
            selected_training=(
                TrainingRead.model_validate(
                    selected_training
                )
            ),
            trainings=[
                TrainingRead.model_validate(
                    x
                )
                for x in trainings
            ],
            rows=rows,
            selected_attendance=(
                selected_attendance
            ),
        )
