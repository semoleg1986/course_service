from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CompleteLessonCommand:
    """Отмечает урок завершенным студентом."""

    course_id: str
    lesson_id: str
    actor_id: str
    actor_roles: list[str]
