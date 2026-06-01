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


@dataclass(frozen=True, slots=True)
class CourseAuthoringLessonResult:
    """Lesson item внутри studio/admin authoring read model."""

    lesson_id: str
    title: str
    description: str | None
    content_type: str
    content_ref: str | None
    duration_minutes: int | None
    is_preview: bool
    released_at: datetime | None
    status: str
    position: int
    version: int
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True, slots=True)
class CourseAuthoringModuleResult:
    """Module item внутри studio/admin authoring read model."""

    module_id: str
    title: str
    description: str | None
    is_required: bool
    released_at: datetime | None
    status: str
    position: int
    lessons_count: int
    lessons: list[CourseAuthoringLessonResult]
    version: int
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True, slots=True)
class CourseAuthoringResult:
    """Полный admin/studio read model курса для редактора."""

    course: CourseResult
    modules: list[CourseAuthoringModuleResult]
    version: int
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True, slots=True)
class AdminCourseListItemResult:
    """Summary курса для admin/studio списка."""

    course_id: str
    title: str
    teacher_id: str
    teacher_display_name: str | None
    slug: str
    publish_state: str
    price: float
    currency: str
    modules_count: int
    lessons_total: int
    published_at: datetime | None
    archived_at: datetime | None
    created_at: datetime
    updated_at: datetime
    version: int


@dataclass(frozen=True, slots=True)
class CourseProgressItemResult:
    """Прогресс ученика по курсу для parent-view."""

    course_id: str
    title: str
    progress_percent: float
    completed_lessons: int
    total_lessons: int
    status: str


@dataclass(frozen=True, slots=True)
class StudentLessonCompletionResult:
    """Результат completion конкретного урока студентом."""

    course_id: str
    module_id: str
    lesson_id: str
    student_id: str
    lesson_status: str
    course_status: str
    progress_percent: float
    completed_lessons: int
    total_lessons: int
    completed_at: datetime | None


@dataclass(frozen=True, slots=True)
class StudentCourseProgressResult:
    """Прогресс текущего студента по одному курсу."""

    course_id: str
    title: str
    progress_percent: float
    completed_lessons: int
    total_lessons: int
    status: str
    completed_at: datetime | None


@dataclass(frozen=True, slots=True)
class StudentCourseLearningProgressResult:
    """Progress summary внутри student learning read model."""

    progress_percent: float
    completed_lessons: int
    total_lessons: int
    status: str
    completed_at: datetime | None


@dataclass(frozen=True, slots=True)
class StudentCourseLearningLessonResult:
    """Student-facing lesson item внутри learning read model."""

    lesson_id: str
    title: str
    description: str | None
    content_type: str
    content_ref: str | None
    duration_minutes: int | None
    is_preview: bool
    progress_status: str
    is_completed: bool


@dataclass(frozen=True, slots=True)
class StudentCourseLearningModuleResult:
    """Student-facing module item внутри learning read model."""

    module_id: str
    title: str
    description: str | None
    is_required: bool
    lessons_count: int
    lessons: list[StudentCourseLearningLessonResult]


@dataclass(frozen=True, slots=True)
class StudentCourseLearningResult:
    """Полный student-facing read model курса."""

    course_id: str
    title: str
    description: str | None
    level: str
    progress: StudentCourseLearningProgressResult
    next_lesson_id: str | None
    modules: list[StudentCourseLearningModuleResult]


@dataclass(frozen=True, slots=True)
class CompletedCourseItemResult:
    """Завершенный курс ученика для parent-view."""

    course_id: str
    title: str
    completed_at: datetime


@dataclass(frozen=True, slots=True)
class PublicCourseModuleResult:
    """Публичное summary модуля курса."""

    module_id: str
    title: str
    lessons_count: int


@dataclass(frozen=True, slots=True)
class PublicCourseCardResult:
    """Краткий DTO опубликованного курса для public catalog."""

    course_id: str
    slug: str
    title: str
    description: str | None
    level: str
    lessons_total: int
    modules_count: int
    cover_image_url: str | None
    is_live_enabled: bool
    teacher_display_name: str | None
    published_at: datetime | None


@dataclass(frozen=True, slots=True)
class PublicCourseResult:
    """DTO опубликованного курса для public response."""

    course_id: str
    slug: str
    title: str
    teacher_id: str
    teacher_display_name: str | None
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
    publish_state: str
    seo_meta_title: str
    seo_meta_description: str
    seo_canonical_url: str | None
    seo_robots: str
    seo_og_image_url: str | None
    modules: list[PublicCourseModuleResult]
