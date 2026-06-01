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
class GetCourseAuthoringQuery:
    """Возвращает полный admin/studio read model курса."""

    course_id: str
    actor_id: str
    actor_roles: list[str]


@dataclass(frozen=True, slots=True)
class ListAdminCoursesQuery:
    """Возвращает admin/studio список курсов."""

    actor_id: str
    actor_roles: list[str]
    publish_state: str | None = None
    teacher_id: str | None = None
    search: str | None = None
    limit: int = 100
    offset: int = 0


@dataclass(frozen=True, slots=True)
class GetPublishedCourseBySlugQuery:
    """Возвращает опубликованный курс по slug для public API."""

    slug: str


@dataclass(frozen=True, slots=True)
class ListPublishedCoursesQuery:
    """Возвращает public catalog опубликованных курсов."""

    limit: int = 100
    offset: int = 0
