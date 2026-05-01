"""Query DTO курса."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class GetCourseByIdQuery:
    """Возвращает курс по ID."""

    course_id: str
    actor_id: str
    actor_roles: list[str]


@dataclass(frozen=True, slots=True)
class GetPublishedCourseBySlugQuery:
    """Возвращает опубликованный курс по slug для public API."""

    slug: str
