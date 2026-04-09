from __future__ import annotations

from datetime import UTC, datetime

import pytest

from src.domain.content.course.entity import Course, Lesson, Module
from src.domain.content.course.value_objects import CourseSlug, SeoMetadata
from src.domain.delivery.access_grant.entity import AccessGrant
from src.domain.delivery.access_grant.value_objects import PaymentConfirmation
from src.domain.delivery.enrollment.entity import Enrollment
from src.domain.errors import InvariantViolationError
from src.domain.shared.entity import EntityMeta


def _now() -> datetime:
    return datetime(2026, 4, 9, tzinfo=UTC)


def _published_course(now: datetime) -> Course:
    course = Course.create(
        course_id="course-1",
        title="Math",
        slug=CourseSlug("math"),
        seo=SeoMetadata(meta_title="Math", meta_description="Math desc"),
        created_at=now,
        created_by="teacher-1",
    )
    module = Module.create(module_id="m-1", title="M", created_at=now, created_by="teacher-1")
    lesson = Lesson.create(lesson_id="l-1", title="L", created_at=now, created_by="teacher-1")
    module.add_lesson(lesson, changed_at=now, changed_by="teacher-1")
    course.add_module(module, changed_at=now, changed_by="teacher-1")
    course.publish(changed_at=now, changed_by="teacher-1")
    return course


def test_entity_meta_archive_and_delete_marks_fields() -> None:
    now = _now()
    meta = EntityMeta.create(at=now, actor_id="u-1")

    meta.mark_archived(at=now, actor_id="u-2")
    assert meta.archived_by == "u-2"

    meta.mark_deleted(at=now, actor_id="u-3")
    assert meta.deleted_by == "u-3"


def test_course_seo_value_object_validation() -> None:
    with pytest.raises(InvariantViolationError):
        CourseSlug("Bad Slug")

    with pytest.raises(InvariantViolationError):
        SeoMetadata(meta_title="", meta_description="desc")
    with pytest.raises(InvariantViolationError):
        SeoMetadata(meta_title="x" * 71, meta_description="desc")
    with pytest.raises(InvariantViolationError):
        SeoMetadata(meta_title="ok", meta_description="x" * 161)
    with pytest.raises(InvariantViolationError):
        SeoMetadata(meta_title="ok", meta_description="desc", robots="nofollow")


def test_access_grant_reject_revoke_and_guards() -> None:
    now = _now()
    grant = AccessGrant.request(
        grant_id="g-1",
        course_id="course-1",
        student_id="student-1",
        requested_at=now,
        requested_by="parent-1",
    )
    grant.reject(changed_at=now, changed_by="admin-1")
    assert grant.status.value == "rejected"

    with pytest.raises(InvariantViolationError):
        grant.mark_paid(
            payment=PaymentConfirmation(
                paid_amount=100,
                currency="USD",
                confirmed_by_admin_id="admin-1",
                confirmed_at=now,
            ),
            changed_at=now,
            changed_by="admin-1",
        )

    grant2 = AccessGrant.request(
        grant_id="g-2",
        course_id="course-1",
        student_id="student-1",
        requested_at=now,
        requested_by="parent-1",
    )
    grant2.mark_paid(
        payment=PaymentConfirmation(
            paid_amount=100,
            currency="USD",
            confirmed_by_admin_id="admin-1",
            confirmed_at=now,
        ),
        changed_at=now,
        changed_by="admin-1",
    )
    grant2.approve(admin_id="admin-1", changed_at=now)
    grant2.revoke(changed_at=now, changed_by="admin-1")
    assert grant2.status.value == "revoked"

    with pytest.raises(InvariantViolationError):
        grant2.reject(changed_at=now, changed_by="admin-1")


def test_enrollment_complete_and_invariant_checks() -> None:
    now = _now()
    course = _published_course(now)
    grant = AccessGrant.request(
        grant_id="g-3",
        course_id="course-1",
        student_id="student-1",
        requested_at=now,
        requested_by="parent-1",
    )

    with pytest.raises(InvariantViolationError):
        Enrollment.create(
            enrollment_id="e-bad",
            course=course,
            grant=grant,
            student_id="student-1",
            created_at=now,
            created_by="student-1",
        )

    grant.mark_paid(
        payment=PaymentConfirmation(
            paid_amount=100,
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
    enrollment.complete(changed_at=now, changed_by="teacher-1")
    assert enrollment.status.value == "completed"
