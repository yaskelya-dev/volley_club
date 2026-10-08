class ServiceError(Exception):
    """Базовое бизнес-исключение. API преобразует его в HTTPException."""


class NotFoundError(ServiceError):
    pass


class AlreadyExistsError(ServiceError):
    pass


class ForbiddenError(ServiceError):
    pass


class InvalidCredentialsError(ServiceError):
    pass


class ValidationServiceError(ServiceError):
    pass
