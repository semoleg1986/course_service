class DomainError(Exception):
    """Базовая ошибка доменного слоя."""


class ValidationError(DomainError):
    """Ошибка валидации входных данных домена."""


class NotFoundError(DomainError):
    """Сущность домена не найдена."""


class AccessDeniedError(DomainError):
    """Операция запрещена политикой доступа."""


class InvariantViolationError(DomainError):
    """
    Ошибка нарушения доменного инварианта.

    :raises InvariantViolationError: Если бизнес-правило агрегата нарушено.
    """
