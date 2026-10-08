from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.models.base import Player, Team, TeamPlayer


class TeamRepositoryProtocol:
    async def list_by_owner(self, user_id: int) -> list[Team]: ...
    async def get_owned(self, team_id: int, user_id: int) -> Team | None: ...
    async def create(self, name: str, user_id: int) -> Team: ...
    async def update(self, team: Team, name: str) -> Team: ...
    async def delete(self, team: Team) -> None: ...
    async def player_is_member(self, team_id: int, player_id: int) -> bool: ...
    async def add_player(self, team_id: int, player_id: int) -> None: ...
    async def remove_player(self, team_id: int, player_id: int) -> None: ...


class TeamRepository(TeamRepositoryProtocol):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_by_owner(self, user_id: int) -> list[Team]:
        result = await self._session.execute(
            select(Team)
            .where(Team.created_by == user_id)
            .options(
                selectinload(Team.players),
                selectinload(Team.trainings),
            )
            .order_by(Team.name)
        )
        return list(result.scalars().unique().all())

    async def get_owned(self, team_id: int, user_id: int) -> Team | None:
        result = await self._session.execute(
            select(Team)
            .where(
                Team.id == team_id,
                Team.created_by == user_id,
            )
            .options(selectinload(Team.players))
        )
        return result.scalar_one_or_none()

    async def create(self, name: str, user_id: int) -> Team:
        team = Team(name=name, created_by=user_id)
        self._session.add(team)
        await self._session.commit()
        await self._session.refresh(team)
        return team

    async def update(self, team: Team, name: str) -> Team:
        team.name = name
        await self._session.commit()
        await self._session.refresh(team)
        return team

    async def delete(self, team: Team) -> None:
        await self._session.delete(team)
        await self._session.commit()

    async def player_is_member(self, team_id: int, player_id: int) -> bool:
        result = await self._session.execute(
            select(TeamPlayer).where(
                TeamPlayer.team_id == team_id,
                TeamPlayer.player_id == player_id,
            )
        )
        return result.scalar_one_or_none() is not None

    async def add_player(self, team_id: int, player_id: int) -> None:
        self._session.add(
            TeamPlayer(
                team_id=team_id,
                player_id=player_id,
            )
        )
        await self._session.commit()

    async def remove_player(self, team_id: int, player_id: int) -> None:
        await self._session.execute(
            delete(TeamPlayer).where(
                TeamPlayer.team_id == team_id,
                TeamPlayer.player_id == player_id,
            )
        )
        await self._session.commit()
