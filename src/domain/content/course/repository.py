from __future__ import annotations

from typing import Protocol

from .entity import Course


class CourseRepository(Protocol):
    """Репозиторий агрегата Course."""

    def get(self, course_id: str) -> Course | None:
        """Получить курс по id. Возвращает None, если курс не найден."""

    def save(self, course: Course) -> None:
        """Сохранить агрегат Course."""
