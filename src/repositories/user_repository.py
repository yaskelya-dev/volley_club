from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.base import User


class UserRepositoryProtocol:
    async def get_by_id(self, user_id: int) -> User | None: ...
    async def get_by_name(self, name: str) -> User | None: ...
    async def create(self, name: str, hash_pass: str) -> User: ...


class UserRepository(UserRepositoryProtocol):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, user_id: int) -> User | None:
        return await self._session.get(User, user_id)

    async def get_by_name(self, name: str) -> User | None:
        result = await self._session.execute(
            select(User).where(User.name == name)
        )
        return result.scalar_one_or_none()

    async def create(self, name: str, hash_pass: str) -> User:
        user = User(name=name, hash_pass=hash_pass)
        self._session.add(user)
        await self._session.commit()
        await self._session.refresh(user)
        return user
