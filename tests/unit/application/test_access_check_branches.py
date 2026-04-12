from __future__ import annotations

from src.application.access.handlers.check_course_access_handler import (
    CheckCourseAccessHandler,
)
from src.application.access.queries.dto import CheckCourseAccessQuery
from src.infrastructure.clock.system_clock import SystemClock
from src.infrastructure.db.inmemory.access_read_model import InMemoryAccessReadModel


def _handler() -> CheckCourseAccessHandler:
    read_model = InMemoryAccessReadModel()
    read_model.seed_course_owner("course-1", "teacher-1")
    read_model.seed_access_grant_status("course-1", "student-1", "approved")
    read_model.seed_enrollment_status("course-1", "student-1", "active")
    return CheckCourseAccessHandler(read_model=read_model, clock=SystemClock())


def test_denies_when_course_missing() -> None:
    handler = _handler()
    result = handler(
        CheckCourseAccessQuery(
            course_id="missing",
            actor_account_id="u-1",
            actor_roles=["student"],
        )
    )
    assert result.decision == "deny"
    assert result.reason_code == "course_not_found"


def test_teacher_owner_allowed() -> None:
    handler = _handler()
    result = handler(
        CheckCourseAccessQuery(
            course_id="course-1",
            actor_account_id="teacher-1",
            actor_roles=["teacher"],
        )
    )
    assert result.decision == "allow"
    assert result.reason_code == "teacher_owner"


def test_role_not_allowed_for_unknown_role() -> None:
    handler = _handler()
    result = handler(
        CheckCourseAccessQuery(
            course_id="course-1",
            actor_account_id="guest-1",
            actor_roles=["guest"],
        )
    )
    assert result.decision == "deny"
    assert result.reason_code == "role_not_allowed"


def test_denies_for_missing_grant_and_enrollment() -> None:
    handler = _handler()
    result = handler(
        CheckCourseAccessQuery(
            course_id="course-1",
            actor_account_id="student-x",
            actor_roles=["student"],
        )
    )
    assert result.reason_code == "access_grant_required"

    result = handler(
        CheckCourseAccessQuery(
            course_id="course-1",
            actor_account_id="student-1",
            actor_roles=["student"],
            student_id="student-1",
            require_active_grant=True,
            require_enrollment=True,
        )
    )
    assert result.reason_code == "student_allowed"
