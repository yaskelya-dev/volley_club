from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.models.base import Player


class PlayerRepositoryProtocol:
    async def list_by_owner(self, user_id: int) -> list[Player]: ...
    async def get_by_id(self, player_id: int) -> Player | None: ...
    async def get_owned(self, player_id: int, user_id: int) -> Player | None: ...
    async def create(self, name: str, user_id: int) -> Player: ...
    async def update(self, player: Player, name: str) -> Player: ...
    async def delete(self, player: Player) -> None: ...


class PlayerRepository(PlayerRepositoryProtocol):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_by_owner(self, user_id: int) -> list[Player]:
        result = await self._session.execute(
            select(Player)
            .where(Player.created_by == user_id)
            .options(selectinload(Player.teams))
            .order_by(Player.name)
        )
        return list(result.scalars().unique().all())

    async def get_by_id(self, player_id: int) -> Player | None:
        return await self._session.get(Player, player_id)

    async def get_owned(self, player_id: int, user_id: int) -> Player | None:
        result = await self._session.execute(
            select(Player).where(
                Player.id == player_id,
                Player.created_by == user_id,
            )
        )
        return result.scalar_one_or_none()

    async def create(self, name: str, user_id: int) -> Player:
        player = Player(name=name, created_by=user_id)
        self._session.add(player)
        await self._session.commit()
        await self._session.refresh(player)
        return player

    async def update(self, player: Player, name: str) -> Player:
        player.name = name
        await self._session.commit()
        await self._session.refresh(player)
        return player

    async def delete(self, player: Player) -> None:
        await self._session.delete(player)
        await self._session.commit()
