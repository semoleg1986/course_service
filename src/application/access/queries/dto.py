"""DTO для query поддомена access."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CheckCourseAccessQuery:
    """Проверка доступа актора к курсу."""

    course_id: str
    actor_account_id: str
    actor_roles: list[str]
    student_id: str | None = None
    require_active_grant: bool = True
    require_enrollment: bool = False
