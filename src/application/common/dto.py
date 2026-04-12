"""Общие DTO application-слоя."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class AccessDecisionResult:
    """Результат проверки доступа к курсу."""

    decision: str
    reason_code: str
    course_id: str
    actor_account_id: str
    student_id: str | None
    grant_status: str | None
    enrollment_status: str | None
    checked_at: datetime


@dataclass(frozen=True, slots=True)
class CourseResult:
    """DTO курса для response моделей interface-слоя."""

    course_id: str
    title: str
    teacher_id: str
    teacher_display_name: str | None
    slug: str
    description: str | None
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
    modules_count: int
    lessons_total: int
    estimated_duration_hours: int
    is_free: bool
    published_at: datetime | None
    published_by_admin_id: str | None
    archived_at: datetime | None
    archived_by: str | None
    publish_state: str
    seo_meta_title: str
    seo_meta_description: str
    seo_canonical_url: str | None
    seo_robots: str
    seo_og_image_url: str | None
