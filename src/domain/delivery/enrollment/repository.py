from __future__ import annotations

from typing import Protocol

from .entity import Enrollment


class EnrollmentRepository(Protocol):
    """Репозиторий агрегата Enrollment."""

    def get(self, enrollment_id: str) -> Enrollment | None:
        """Получить enrollment по id."""

    def save(self, enrollment: Enrollment) -> None:
        """Сохранить агрегат Enrollment."""
