from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class GetStudentCourseProgressQuery:
    """Возвращает прогресс текущего студента по курсу."""

    course_id: str
    actor_id: str
    actor_roles: list[str]
