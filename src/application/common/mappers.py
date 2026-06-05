"""Мапперы application DTO."""

from __future__ import annotations

from src.application.common.dto import (
    AdminCourseListItemResult,
    CourseAuthoringLessonResult,
    CourseAuthoringModuleResult,
    CourseAuthoringReadinessCheckResult,
    CourseAuthoringReadinessResult,
    CourseAuthoringResult,
    CourseResult,
    PublicCourseCardResult,
    PublicCourseModuleResult,
    PublicCourseResult,
)
from src.domain.content.course.entity import Course
from src.domain.shared.statuses import PublishState


def to_course_result(course: Course) -> CourseResult:
    """Преобразует агрегат Course в CourseResult."""

    return CourseResult(
        course_id=course.course_id,
        title=course.title,
        teacher_id=course.teacher_id,
        teacher_display_name=course.teacher_display_name,
        slug=course.slug.value,
        description=getattr(course, "description", None),
        starts_at=course.schedule.starts_at,
        duration_days=course.schedule.duration_days,
        access_ttl_days=course.schedule.access_ttl_days,
        enrollment_opens_at=course.schedule.enrollment_opens_at,
        enrollment_closes_at=course.schedule.enrollment_closes_at,
        price=course.pricing.price,
        currency=course.pricing.currency,
        language=course.audience.language,
        age_min=course.audience.age_min,
        age_max=course.audience.age_max,
        level=course.audience.level,
        tags=list(course.delivery.tags),
        cover_image_url=course.delivery.cover_image_url,
        is_live_enabled=course.delivery.is_live_enabled,
        live_room_template_id=course.delivery.live_room_template_id,
        timezone=course.schedule.timezone,
        max_students=course.audience.max_students,
        modules_count=course.modules_count,
        lessons_total=course.lessons_total,
        estimated_duration_hours=course.estimated_duration_hours,
        is_free=course.is_free,
        published_at=course.published_at,
        published_by_admin_id=course.published_by_admin_id,
        archived_at=course.archived_at,
        archived_by=course.archived_by,
        publish_state=course.publish_state.value,
        seo_meta_title=course.seo.meta_title,
        seo_meta_description=course.seo.meta_description,
        seo_canonical_url=course.seo.canonical_url,
        seo_robots=course.seo.robots,
        seo_og_image_url=course.seo.og_image_url,
    )


def to_course_authoring_result(course: Course) -> CourseAuthoringResult:
    """Преобразует Course в полный admin/studio authoring read model."""

    published_modules = [
        module for module in course.modules if module.status == PublishState.PUBLISHED
    ]
    published_modules_with_lessons = [
        module
        for module in published_modules
        if any(lesson.status == PublishState.PUBLISHED for lesson in module.lessons)
    ]
    seo_ready = bool(
        course.slug.value and course.seo.meta_title and course.seo.meta_description
    )
    readiness_checks = [
        CourseAuthoringReadinessCheckResult(
            code="has_module",
            label="Добавлен хотя бы один модуль",
            passed=bool(course.modules),
            detail=None if course.modules else "Добавьте модуль в структуру курса.",
        ),
        CourseAuthoringReadinessCheckResult(
            code="has_published_module",
            label="Есть published-модуль",
            passed=bool(published_modules),
            detail=(
                None
                if published_modules
                else "Переведите минимум один модуль в статус published."
            ),
        ),
        CourseAuthoringReadinessCheckResult(
            code="published_modules_have_lessons",
            label="В каждом published-модуле есть published-урок",
            passed=bool(published_modules)
            and len(published_modules) == len(published_modules_with_lessons),
            detail=(
                None
                if published_modules
                and len(published_modules) == len(published_modules_with_lessons)
                else "Добавьте и опубликуйте уроки в published-модулях."
            ),
        ),
        CourseAuthoringReadinessCheckResult(
            code="seo_minimum",
            label="Заполнен SEO-минимум",
            passed=seo_ready,
            detail=None if seo_ready else "Нужны slug, meta title и meta description.",
        ),
    ]
    readiness = CourseAuthoringReadinessResult(
        ready_to_publish=all(check.passed for check in readiness_checks),
        checks=readiness_checks,
    )
    has_unpublished_changes = (
        course.publish_state != PublishState.PUBLISHED
        or course.published_at is None
        or course.meta.updated_at > course.published_at
    )

    modules = [
        CourseAuthoringModuleResult(
            module_id=module.module_id,
            title=module.title,
            description=module.description,
            is_required=module.is_required,
            released_at=module.released_at,
            status=module.status.value,
            position=module_position,
            lessons_count=len(module.lessons),
            lessons=[
                CourseAuthoringLessonResult(
                    lesson_id=lesson.lesson_id,
                    title=lesson.title,
                    description=lesson.description,
                    content_type=lesson.content_type,
                    content_ref=lesson.content_ref,
                    duration_minutes=lesson.duration_minutes,
                    is_preview=lesson.is_preview,
                    released_at=lesson.released_at,
                    status=lesson.status.value,
                    position=lesson_position,
                    version=lesson.meta.version,
                    created_at=lesson.meta.created_at,
                    created_by=lesson.meta.created_by,
                    updated_at=lesson.meta.updated_at,
                    updated_by=lesson.meta.updated_by,
                )
                for lesson_position, lesson in enumerate(module.lessons, start=1)
            ],
            version=module.meta.version,
            created_at=module.meta.created_at,
            created_by=module.meta.created_by,
            updated_at=module.meta.updated_at,
            updated_by=module.meta.updated_by,
        )
        for module_position, module in enumerate(course.modules, start=1)
    ]
    return CourseAuthoringResult(
        course=to_course_result(course),
        modules=modules,
        readiness=readiness,
        has_unpublished_changes=has_unpublished_changes,
        draft_version=course.meta.version,
        published_version=(
            course.meta.version
            if course.publish_state == PublishState.PUBLISHED
            and not has_unpublished_changes
            else None
        ),
        version=course.meta.version,
        created_at=course.meta.created_at,
        updated_at=course.meta.updated_at,
    )


def to_admin_course_list_item_result(course: Course) -> AdminCourseListItemResult:
    """Преобразует Course в summary для admin/studio списка."""

    return AdminCourseListItemResult(
        course_id=course.course_id,
        title=course.title,
        teacher_id=course.teacher_id,
        teacher_display_name=course.teacher_display_name,
        slug=course.slug.value,
        publish_state=course.publish_state.value,
        price=course.pricing.price,
        currency=course.pricing.currency,
        modules_count=course.modules_count,
        lessons_total=course.lessons_total,
        published_at=course.published_at,
        archived_at=course.archived_at,
        created_at=course.meta.created_at,
        created_by=course.meta.created_by,
        updated_at=course.meta.updated_at,
        updated_by=course.meta.updated_by,
        version=course.meta.version,
    )


def to_public_course_result(course: Course) -> PublicCourseResult:
    """Преобразует опубликованный Course в public DTO."""

    published_modules = [
        PublicCourseModuleResult(
            module_id=module.module_id,
            title=module.title,
            lessons_count=len(
                [
                    lesson
                    for lesson in module.lessons
                    if lesson.status == PublishState.PUBLISHED
                ]
            ),
        )
        for module in course.modules
        if module.status == PublishState.PUBLISHED
    ]

    return PublicCourseResult(
        course_id=course.course_id,
        slug=course.slug.value,
        title=course.title,
        teacher_id=course.teacher_id,
        teacher_display_name=course.teacher_display_name,
        description=getattr(course, "description", None),
        starts_at=course.schedule.starts_at,
        duration_days=course.schedule.duration_days,
        access_ttl_days=course.schedule.access_ttl_days,
        enrollment_opens_at=course.schedule.enrollment_opens_at,
        enrollment_closes_at=course.schedule.enrollment_closes_at,
        price=course.pricing.price,
        currency=course.pricing.currency,
        language=course.audience.language,
        age_min=course.audience.age_min,
        age_max=course.audience.age_max,
        level=course.audience.level,
        tags=list(course.delivery.tags),
        cover_image_url=course.delivery.cover_image_url,
        is_live_enabled=course.delivery.is_live_enabled,
        live_room_template_id=course.delivery.live_room_template_id,
        timezone=course.schedule.timezone,
        max_students=course.audience.max_students,
        modules_count=course.modules_count,
        lessons_total=course.lessons_total,
        estimated_duration_hours=course.estimated_duration_hours,
        is_free=course.is_free,
        published_at=course.published_at,
        publish_state=course.publish_state.value,
        seo_meta_title=course.seo.meta_title,
        seo_meta_description=course.seo.meta_description,
        seo_canonical_url=course.seo.canonical_url,
        seo_robots=course.seo.robots,
        seo_og_image_url=course.seo.og_image_url,
        modules=published_modules,
    )


def to_public_course_card_result(course: Course) -> PublicCourseCardResult:
    """Преобразует опубликованный Course в summary DTO для public catalog."""

    return PublicCourseCardResult(
        course_id=course.course_id,
        slug=course.slug.value,
        title=course.title,
        description=getattr(course, "description", None),
        level=course.audience.level,
        lessons_total=course.lessons_total,
        modules_count=course.modules_count,
        cover_image_url=course.delivery.cover_image_url,
        is_live_enabled=course.delivery.is_live_enabled,
        teacher_display_name=course.teacher_display_name,
        published_at=course.published_at,
    )
