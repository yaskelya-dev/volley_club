import bcrypt

from src.repositories.user_repository import UserRepositoryProtocol
from src.schemas.user import UserRead
from src.services import (
    AlreadyExistsError,
    InvalidCredentialsError,
    NotFoundError,
    ValidationServiceError,
)


class UserService:
    def __init__(self, repository: UserRepositoryProtocol) -> None:
        self._repository = repository

    async def register(
        self,
        name: str,
        password: str,
    ) -> UserRead:
        name = name.strip()

        if not name or len(name) < 2:
            raise ValidationServiceError(
                "Имя пользователя слишком короткое."
            )

        if len(password) < 6:
            raise ValidationServiceError(
                "Пароль должен содержать минимум 6 символов."
            )

        if len(password) > 72:
            raise ValidationServiceError(
                "Пароль не должен превышать 72 символа."
            )

        if await self._repository.get_by_name(name):
            raise AlreadyExistsError(
                "Пользователь с таким именем уже существует."
            )

        try:
            hashed = bcrypt.hashpw(
                password.encode("utf-8"),
                bcrypt.gensalt(),
            ).decode("utf-8")

            user = await self._repository.create(
                name,
                hashed,
            )

            return UserRead.model_validate(user)

        except ValueError as exc:
            raise ValidationServiceError(
                "Не удалось обработать пароль."
            ) from exc

    async def login(
        self,
        name: str,
        password: str,
    ) -> UserRead:
        user = await self._repository.get_by_name(name.strip())

        if user is None or not bcrypt.checkpw(
            password.encode("utf-8"),
            user.hash_pass.encode("utf-8"),
        ):
            raise InvalidCredentialsError(
                "Неверное имя пользователя или пароль."
            )

        return UserRead.model_validate(user)

    async def get_by_id(
        self,
        user_id: int,
    ) -> UserRead:
        user = await self._repository.get_by_id(user_id)

        if user is None:
            raise NotFoundError(
                "Пользователь не найден."
            )

        return UserRead.model_validate(user)
