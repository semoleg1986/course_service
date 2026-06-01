from __future__ import annotations

from typing import Protocol

from .entity import Course


class CourseRepository(Protocol):
    """Репозиторий агрегата Course."""

    def get(self, course_id: str) -> Course | None:
        """Получить курс по id. Возвращает None, если курс не найден."""

    def get_by_slug(self, slug: str) -> Course | None:
        """Получить курс по slug. Возвращает None, если курс не найден."""

    def list_published(self, *, limit: int = 100, offset: int = 0) -> list[Course]:
        """Вернуть опубликованные курсы для public catalog."""

    def list_admin(
        self,
        *,
        publish_state: str | None = None,
        teacher_id: str | None = None,
        search: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Course]:
        """Вернуть курсы для admin/studio списка."""

    def save(self, course: Course) -> None:
        """Сохранить агрегат Course."""
