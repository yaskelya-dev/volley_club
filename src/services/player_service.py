from src.repositories.player_repository import PlayerRepositoryProtocol
from src.schemas.player import PlayerCreate, PlayerRead, PlayerUpdate
from src.services import NotFoundError, ValidationServiceError


class PlayerService:
    def __init__(
        self,
        repository: PlayerRepositoryProtocol,
    ) -> None:
        self._repository = repository

    async def list(
        self,
        user_id: int,
    ) -> list[PlayerRead]:
        players = await self._repository.list_by_owner(user_id)

        return [
            PlayerRead.model_validate(player)
            for player in players
        ]

    async def get(
        self,
        user_id: int,
        player_id: int,
    ) -> PlayerRead:
        player = await self._repository.get_owned(
            player_id,
            user_id,
        )

        if player is None:
            raise NotFoundError("Игрок не найден.")

        return PlayerRead.model_validate(player)

    async def create(
        self,
        user_id: int,
        payload: PlayerCreate,
    ) -> PlayerRead:
        name = payload.name.strip()

        if not name:
            raise ValidationServiceError(
                "Имя игрока не может быть пустым."
            )

        player = await self._repository.create(
            name,
            user_id,
        )

        return PlayerRead.model_validate(player)

    async def update(
        self,
        user_id: int,
        player_id: int,
        payload: PlayerUpdate,
    ) -> PlayerRead:
        player = await self._repository.get_owned(
            player_id,
            user_id,
        )

        if player is None:
            raise NotFoundError("Игрок не найден.")

        name = payload.name.strip()

        if not name:
            raise ValidationServiceError(
                "Имя игрока не может быть пустым."
            )

        player = await self._repository.update(
            player,
            name,
        )

        return PlayerRead.model_validate(player)

    async def delete(
        self,
        user_id: int,
        player_id: int,
    ) -> None:
        player = await self._repository.get_owned(
            player_id,
            user_id,
        )

        if player is None:
            raise NotFoundError("Игрок не найден.")

        await self._repository.delete(player)
