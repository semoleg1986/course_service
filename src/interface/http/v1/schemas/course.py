"""Схемы API курса."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field, field_validator


def _ensure_tz_aware(value: datetime | None, field_name: str) -> datetime | None:
    """Проверяет, что datetime содержит timezone offset."""
    if value is None:
        return None
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} должен содержать timezone offset")
    return value


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

    @field_validator(
        "starts_at", "enrollment_opens_at", "enrollment_closes_at", mode="after"
    )
    @classmethod
    def ensure_datetime_has_timezone(
        cls, value: datetime | None, info: object
    ) -> datetime | None:
        field_name = getattr(info, "field_name", "datetime")
        return _ensure_tz_aware(value, field_name)


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

    @field_validator(
        "starts_at", "enrollment_opens_at", "enrollment_closes_at", mode="after"
    )
    @classmethod
    def ensure_datetime_has_timezone(
        cls, value: datetime | None, info: object
    ) -> datetime | None:
        field_name = getattr(info, "field_name", "datetime")
        return _ensure_tz_aware(value, field_name)


class AddModuleRequest(BaseModel):
    """Запрос добавления модуля в курс."""

    module_id: str | None = None
    title: str
    description: str | None = None
    is_required: bool = True
    released_at: datetime | None = None


class AddLessonRequest(BaseModel):
    """Запрос добавления урока в модуль."""

    lesson_id: str | None = None
    title: str
    description: str | None = None
    content_type: str = Field(default="video")
    content_ref: str | None = None
    duration_minutes: int | None = Field(default=None, ge=1)
    is_preview: bool = False
    released_at: datetime | None = None


class UpdateModuleRequest(BaseModel):
    """Запрос обновления модуля."""

    title: str | None = None
    description: str | None = None
    is_required: bool | None = None
    released_at: datetime | None = None
    status: str | None = None


class UpdateLessonRequest(BaseModel):
    """Запрос обновления урока."""

    title: str | None = None
    description: str | None = None
    content_type: str | None = None
    content_ref: str | None = None
    duration_minutes: int | None = Field(default=None, ge=1)
    is_preview: bool | None = None
    released_at: datetime | None = None
    status: str | None = None


class SeoResponse(BaseModel):
    """SEO поля курса в response."""

    meta_title: str
    meta_description: str
    canonical_url: str | None = None
    robots: str
    og_image_url: str | None = None


class PublicCourseModuleResponse(BaseModel):
    """Краткая структура опубликованного модуля."""

    module_id: str
    title: str
    lessons_count: int = Field(ge=0)


class CourseResponse(BaseModel):
    """Ответ курса."""

    course_id: str
    title: str
    teacher_id: str
    teacher_display_name: str | None
    slug: str
    description: str | None
    starts_at: datetime
    starts_at_local: datetime | None = None
    duration_days: int
    access_ttl_days: int | None
    enrollment_opens_at: datetime | None
    enrollment_opens_at_local: datetime | None = None
    enrollment_closes_at: datetime | None
    enrollment_closes_at_local: datetime | None = None
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
    viewer_timezone: str | None = None
    seo: SeoResponse


class PublicCourseResponse(BaseModel):
    """Публичный response опубликованного курса."""

    course_id: str
    slug: str
    title: str
    teacher_id: str
    teacher_display_name: str | None
    description: str | None
    starts_at: datetime
    starts_at_local: datetime | None = None
    duration_days: int
    access_ttl_days: int | None
    enrollment_opens_at: datetime | None
    enrollment_opens_at_local: datetime | None = None
    enrollment_closes_at: datetime | None
    enrollment_closes_at_local: datetime | None = None
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
    publish_state: str
    viewer_timezone: str | None = None
    seo: SeoResponse
    modules: list[PublicCourseModuleResponse]


class CourseProgressItemResponse(BaseModel):
    """Элемент прогресса ученика по курсу."""

    course_id: str
    title: str
    progress_percent: float = Field(ge=0, le=100)
    completed_lessons: int = Field(ge=0)
    total_lessons: int = Field(ge=0)
    status: str


class CompletedCourseItemResponse(BaseModel):
    """Элемент завершенного курса ученика."""

    course_id: str
    title: str
    completed_at: datetime
    completed_at_local: datetime | None = None


class CourseProgressListResponse(BaseModel):
    """Список прогресса ученика по курсам."""

    items: list[CourseProgressItemResponse]
    limit: int
    offset: int
    status: str | None = None
    viewer_timezone: str | None = None


class CompletedCourseListResponse(BaseModel):
    """Список завершенных курсов ученика."""

    items: list[CompletedCourseItemResponse]
    limit: int
    offset: int
    viewer_timezone: str | None = None


class StudentLessonCompletionResponse(BaseModel):
    """Ответ student endpoint после completion урока."""

    course_id: str
    module_id: str
    lesson_id: str
    student_id: str
    lesson_status: str
    course_status: str
    progress_percent: float = Field(ge=0, le=100)
    completed_lessons: int = Field(ge=0)
    total_lessons: int = Field(ge=0)
    completed_at: datetime | None


class StudentCourseProgressResponse(BaseModel):
    """Ответ student progress endpoint."""

    course_id: str
    title: str
    progress_percent: float = Field(ge=0, le=100)
    completed_lessons: int = Field(ge=0)
    total_lessons: int = Field(ge=0)
    status: str
    completed_at: datetime | None
