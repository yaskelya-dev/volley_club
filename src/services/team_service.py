from src.repositories.player_repository import PlayerRepositoryProtocol
from src.repositories.team_repository import TeamRepositoryProtocol
from src.schemas.team import (
    TeamCreate,
    TeamDetail,
    TeamRead,
    TeamUpdate,
)
from src.services import (
    AlreadyExistsError,
    NotFoundError,
    ValidationServiceError,
)


class TeamService:
    def __init__(
        self,
        repository: TeamRepositoryProtocol,
        player_repository: PlayerRepositoryProtocol,
    ) -> None:
        self._repository = repository
        self._player_repository = player_repository

    async def list(
        self,
        user_id: int,
    ) -> list[TeamDetail]:
        result: list[TeamDetail] = []

        for team in await self._repository.list_by_owner(user_id):
            result.append(
                TeamDetail.model_validate(team)
            )

        return result

    async def get(
        self,
        user_id: int,
        team_id: int,
    ) -> TeamDetail:
        team = await self._repository.get_owned(
            team_id,
            user_id,
        )

        if team is None:
            raise NotFoundError("Команда не найдена.")

        return TeamDetail.model_validate(team)

    async def create(
        self,
        user_id: int,
        payload: TeamCreate,
    ) -> TeamRead:
        name = payload.name.strip()

        if not name:
            raise ValidationServiceError(
                "Название команды не может быть пустым."
            )

        team = await self._repository.create(
            name,
            user_id,
        )

        return TeamRead.model_validate(team)

    async def update(
        self,
        user_id: int,
        team_id: int,
        payload: TeamUpdate,
    ) -> TeamRead:
        team = await self._repository.get_owned(
            team_id,
            user_id,
        )

        if team is None:
            raise NotFoundError("Команда не найдена.")

        name = payload.name.strip()

        if not name:
            raise ValidationServiceError(
                "Название команды не может быть пустым."
            )

        team = await self._repository.update(
            team,
            name,
        )

        return TeamRead.model_validate(team)

    async def delete(
        self,
        user_id: int,
        team_id: int,
    ) -> None:
        team = await self._repository.get_owned(
            team_id,
            user_id,
        )

        if team is None:
            raise NotFoundError("Команда не найдена.")

        await self._repository.delete(team)

    async def add_player(
        self,
        user_id: int,
        team_id: int,
        player_id: int,
    ) -> None:
        team = await self._repository.get_owned(
            team_id,
            user_id,
        )

        if team is None:
            raise NotFoundError("Команда не найдена.")

        player = await self._player_repository.get_owned(
            player_id,
            user_id,
        )

        if player is None:
            raise NotFoundError("Игрок не найден.")

        if await self._repository.player_is_member(
            team_id,
            player_id,
        ):
            raise AlreadyExistsError(
                "Игрок уже входит в команду."
            )

        await self._repository.add_player(
            team_id,
            player_id,
        )

    async def remove_player(
        self,
        user_id: int,
        team_id: int,
        player_id: int,
    ) -> None:
        team = await self._repository.get_owned(
            team_id,
            user_id,
        )

        if team is None:
            raise NotFoundError("Команда не найдена.")

        player = await self._player_repository.get_owned(
            player_id,
            user_id,
        )

        if player is None:
            raise NotFoundError("Игрок не найден.")

        if not await self._repository.player_is_member(
            team_id,
            player_id,
        ):
            raise NotFoundError(
                "Игрок не состоит в команде."
            )

        await self._repository.remove_player(
            team_id,
            player_id,
        )
