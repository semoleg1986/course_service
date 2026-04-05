class DomainError(Exception):
    """Базовая ошибка доменного слоя."""


class InvariantViolationError(DomainError):
    """
    Ошибка нарушения доменного инварианта.

    :raises InvariantViolationError: Если бизнес-правило агрегата нарушено.
    """
