"""Мапперы application DTO."""

from __future__ import annotations

from src.application.common.dto import CourseResult
from src.domain.content.course.entity import Course


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
