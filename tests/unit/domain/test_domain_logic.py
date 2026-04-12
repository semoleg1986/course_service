from datetime import UTC, datetime

import pytest

from src.domain.content.course.entity import Course, Lesson, Module
from src.domain.content.course.value_objects import (
    CourseSchedule,
    CourseSlug,
    SeoMetadata,
)
from src.domain.delivery.access_grant.entity import AccessGrant
from src.domain.delivery.access_grant.value_objects import PaymentConfirmation
from src.domain.delivery.enrollment.entity import Enrollment
from src.domain.errors import InvariantViolationError


def _course_with_single_lesson(now: datetime) -> Course:
    course = Course.create(
        course_id="course-1",
        title="Math 1",
        description="Math course",
        teacher_id="teacher-1",
        slug=CourseSlug("math-1"),
        schedule=CourseSchedule(starts_at=now, duration_days=30),
        seo=SeoMetadata(meta_title="Math 1", meta_description="Math course"),
        created_at=now,
        created_by="teacher-1",
    )
    module = Module.create(
        module_id="m-1",
        title="Numbers",
        created_at=now,
        created_by="teacher-1",
    )
    lesson = Lesson.create(
        lesson_id="l-1",
        title="Intro",
        created_at=now,
        created_by="teacher-1",
    )
    module.add_lesson(lesson, changed_at=now, changed_by="teacher-1")
    course.add_module(module, changed_at=now, changed_by="teacher-1")
    return course


def test_publish_requires_module_with_lesson() -> None:
    now = datetime.now(UTC)
    course = Course.create(
        course_id="course-1",
        title="Math 1",
        description="Math course",
        teacher_id="teacher-1",
        slug=CourseSlug("math-1"),
        schedule=CourseSchedule(starts_at=now, duration_days=30),
        seo=SeoMetadata(meta_title="Math 1", meta_description="Math course"),
        created_at=now,
        created_by="teacher-1",
    )

    with pytest.raises(InvariantViolationError):
        course.publish(changed_at=now, changed_by="teacher-1")


def test_access_grant_must_be_paid_before_approval() -> None:
    now = datetime.now(UTC)
    grant = AccessGrant.request(
        grant_id="g-1",
        course_id="course-1",
        student_id="student-1",
        requested_at=now,
        requested_by="parent-1",
    )

    with pytest.raises(InvariantViolationError):
        grant.approve(admin_id="admin-1", changed_at=now)


def test_enrollment_requires_approved_grant() -> None:
    now = datetime.now(UTC)
    course = _course_with_single_lesson(now)
    course.publish(changed_at=now, changed_by="teacher-1")

    grant = AccessGrant.request(
        grant_id="g-1",
        course_id="course-1",
        student_id="student-1",
        requested_at=now,
        requested_by="parent-1",
    )
    grant.mark_paid(
        PaymentConfirmation(
            paid_amount=120.0,
            currency="USD",
            confirmed_by_admin_id="admin-1",
            confirmed_at=now,
        ),
        changed_at=now,
        changed_by="admin-1",
    )
    grant.approve(admin_id="admin-1", changed_at=now)

    enrollment = Enrollment.create(
        enrollment_id="e-1",
        course=course,
        grant=grant,
        student_id="student-1",
        created_at=now,
        created_by="student-1",
    )

    assert enrollment.course_id == "course-1"
    assert enrollment.student_id == "student-1"


def test_meta_version_increments_on_mutation() -> None:
    now = datetime.now(UTC)
    grant = AccessGrant.request(
        grant_id="g-1",
        course_id="course-1",
        student_id="student-1",
        requested_at=now,
        requested_by="parent-1",
    )
    v1 = grant.meta.version

    grant.mark_paid(
        PaymentConfirmation(
            paid_amount=120.0,
            currency="USD",
            confirmed_by_admin_id="admin-1",
            confirmed_at=now,
        ),
        changed_at=now,
        changed_by="admin-1",
    )

    assert grant.meta.version == v1 + 1


def test_course_lessons_total_equals_estimated_hours() -> None:
    now = datetime.now(UTC)
    course = _course_with_single_lesson(now)

    assert course.modules_count == 1
    assert course.lessons_total == 1
    assert course.estimated_duration_hours == 1
    assert course.is_free
