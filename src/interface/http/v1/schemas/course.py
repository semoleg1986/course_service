"""Схемы API курса."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class SeoPayload(BaseModel):
    """SEO payload курса."""

    meta_title: str | None = Field(default=None, max_length=70)
    meta_description: str | None = Field(default=None, max_length=160)
    canonical_url: str | None = None
    robots: str = Field(default="index")
    og_image_url: str | None = None


class CreateCourseRequest(BaseModel):
    """Запрос создания курса."""

    title: str
    description: str | None = None
    teacher_id: str
    teacher_display_name: str | None = None
    starts_at: datetime
    duration_days: int = Field(..., ge=1)
    access_ttl_days: int | None = Field(default=None, ge=1)
    enrollment_opens_at: datetime | None = None
    enrollment_closes_at: datetime | None = None
    price: float = Field(default=0, ge=0)
    currency: str = Field(default="USD", min_length=3, max_length=3)
    language: str = Field(default="ru")
    age_min: int | None = Field(default=None, ge=0)
    age_max: int | None = Field(default=None, ge=0)
    level: str = Field(default="beginner")
    tags: list[str] = Field(default_factory=list)
    cover_image_url: str | None = None
    is_live_enabled: bool = False
    live_room_template_id: str | None = None
    timezone: str = Field(default="UTC")
    max_students: int | None = Field(default=None, ge=1)
    slug: str | None = None
    seo: SeoPayload | None = None


class UpdateCourseRequest(BaseModel):
    """Запрос обновления курса."""

    title: str | None = None
    description: str | None = None
    teacher_id: str | None = None
    teacher_display_name: str | None = None
    starts_at: datetime | None = None
    duration_days: int | None = Field(default=None, ge=1)
    access_ttl_days: int | None = Field(default=None, ge=1)
    enrollment_opens_at: datetime | None = None
    enrollment_closes_at: datetime | None = None
    price: float | None = Field(default=None, ge=0)
    currency: str | None = Field(default=None, min_length=3, max_length=3)
    language: str | None = None
    age_min: int | None = Field(default=None, ge=0)
    age_max: int | None = Field(default=None, ge=0)
    level: str | None = None
    tags: list[str] | None = None
    cover_image_url: str | None = None
    is_live_enabled: bool | None = None
    live_room_template_id: str | None = None
    timezone: str | None = None
    max_students: int | None = Field(default=None, ge=1)
    slug: str | None = None
    seo: SeoPayload | None = None


class SeoResponse(BaseModel):
    """SEO поля курса в response."""

    meta_title: str
    meta_description: str
    canonical_url: str | None = None
    robots: str
    og_image_url: str | None = None


class CourseResponse(BaseModel):
    """Ответ курса."""

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
    seo: SeoResponse
