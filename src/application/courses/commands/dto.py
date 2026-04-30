"""Command DTO курса."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class CreateCourseCommand:
    """Создает курс."""

    title: str
    description: str | None
    teacher_id: str
    teacher_display_name: str | None
    starts_at: datetime
    duration_days: int
    access_ttl_days: int | None
    enrollment_opens_at: datetime | None
    enrollment_closes_at: datetime | None
    price: float
    currency: str
    language: str
    age_min: int | None
    age_max: int | None
    level: str
    tags: list[str]
    cover_image_url: str | None
    is_live_enabled: bool
    live_room_template_id: str | None
    timezone: str
    max_students: int | None
    slug: str | None
    seo_meta_title: str | None
    seo_meta_description: str | None
    seo_canonical_url: str | None
    seo_robots: str
    seo_og_image_url: str | None
    actor_id: str
    actor_roles: list[str]


@dataclass(frozen=True, slots=True)
class UpdateCourseCommand:
    """Обновляет курс."""

    course_id: str
    actor_id: str
    actor_roles: list[str]
    title: str | None = None
    description: str | None = None
    teacher_id: str | None = None
    teacher_display_name: str | None = None
    starts_at: datetime | None = None
    duration_days: int | None = None
    access_ttl_days: int | None = None
    enrollment_opens_at: datetime | None = None
    enrollment_closes_at: datetime | None = None
    price: float | None = None
    currency: str | None = None
    language: str | None = None
    age_min: int | None = None
    age_max: int | None = None
    level: str | None = None
    tags: list[str] | None = None
    cover_image_url: str | None = None
    is_live_enabled: bool | None = None
    live_room_template_id: str | None = None
    timezone: str | None = None
    max_students: int | None = None
    slug: str | None = None
    seo_meta_title: str | None = None
    seo_meta_description: str | None = None
    seo_canonical_url: str | None = None
    seo_robots: str | None = None
    seo_og_image_url: str | None = None


@dataclass(frozen=True, slots=True)
class AddModuleCommand:
    """Добавляет модуль в курс."""

    course_id: str
    module_id: str | None
    title: str
    actor_id: str
    actor_roles: list[str]


@dataclass(frozen=True, slots=True)
class AddLessonCommand:
    """Добавляет урок в модуль курса."""

    course_id: str
    module_id: str
    lesson_id: str | None
    title: str
    actor_id: str
    actor_roles: list[str]


@dataclass(frozen=True, slots=True)
class PublishCourseCommand:
    """Публикует курс."""

    course_id: str
    actor_id: str
    actor_roles: list[str]


@dataclass(frozen=True, slots=True)
class ArchiveCourseCommand:
    """Архивирует курс."""

    course_id: str
    actor_id: str
    actor_roles: list[str]
