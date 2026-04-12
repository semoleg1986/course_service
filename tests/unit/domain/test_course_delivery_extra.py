from __future__ import annotations

from datetime import UTC, datetime

import pytest

from src.domain.content.course.entity import Course, Lesson, Module
from src.domain.content.course.value_objects import CourseSchedule, CourseSlug, SeoMetadata
from src.domain.delivery.access_grant.entity import AccessGrant
from src.domain.delivery.access_grant.value_objects import PaymentConfirmation
from src.domain.delivery.enrollment.entity import Enrollment
from src.domain.errors import InvariantViolationError


def _now() -> datetime:
    return datetime(2026, 4, 9, tzinfo=UTC)


def _course(now: datetime) -> Course:
    course = Course.create(
        course_id="course-1",
        title="Math",
        teacher_id="teacher-1",
        slug=CourseSlug("math"),
        schedule=CourseSchedule(starts_at=now, duration_days=21),
        seo=SeoMetadata(meta_title="Math", meta_description="Desc"),
        created_at=now,
        created_by="teacher-1",
    )
    module = Module.create("m-1", "Module", now, "teacher-1")
    module.add_lesson(Lesson.create("l-1", "Lesson", now, "teacher-1"), now, "teacher-1")
    course.add_module(module, now, "teacher-1")
    return course


def test_course_publish_seo_guard_and_archive() -> None:
    now = _now()
    course = _course(now)

    # ломаем SEO минимальный контракт для покрытия инварианта публикации
    object.__setattr__(course.seo, "meta_description", "")
    with pytest.raises(InvariantViolationError):
        course.publish(changed_at=now, changed_by="teacher-1")

    object.__setattr__(course.seo, "meta_description", "Desc")
    course.publish(changed_at=now, changed_by="teacher-1")
    course.archive(changed_at=now, changed_by="teacher-1")
    assert course.publish_state.value == "archived"


def test_payment_confirmation_and_enrollment_mismatch_guards() -> None:
    now = _now()

    with pytest.raises(InvariantViolationError):
        PaymentConfirmation(
            paid_amount=-1,
            currency="USD",
            confirmed_by_admin_id="admin-1",
            confirmed_at=now,
        )
    with pytest.raises(InvariantViolationError):
        PaymentConfirmation(
            paid_amount=10,
            currency="US",
            confirmed_by_admin_id="admin-1",
            confirmed_at=now,
        )

    course = _course(now)
    grant = AccessGrant.request(
        grant_id="g-1",
        course_id="course-2",
        student_id="student-2",
        requested_at=now,
        requested_by="parent-1",
    )

    with pytest.raises(InvariantViolationError):
        Enrollment.create(
            enrollment_id="e-1",
            course=course,
            grant=grant,
            student_id="student-1",
            created_at=now,
            created_by="student-1",
        )
