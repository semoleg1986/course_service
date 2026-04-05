from src.application.access.handlers.check_course_access_handler import (
    CheckCourseAccessHandler,
)
from src.application.access.queries.dto import CheckCourseAccessQuery
from src.infrastructure.clock.system_clock import SystemClock
from src.infrastructure.db.inmemory.access_read_model import InMemoryAccessReadModel


def _build_handler() -> CheckCourseAccessHandler:
    read_model = InMemoryAccessReadModel()
    read_model.seed_course_owner("course-1", "teacher-1")
    read_model.seed_access_grant_status("course-1", "student-1", "approved")
    read_model.seed_enrollment_status("course-1", "student-1", "active")
    return CheckCourseAccessHandler(read_model=read_model, clock=SystemClock())


def test_admin_has_override_access() -> None:
    result = _build_handler()(
        CheckCourseAccessQuery(
            course_id="course-1",
            actor_account_id="admin-1",
            actor_roles=["admin"],
        )
    )

    assert result.decision == "allow"
    assert result.reason_code == "admin_override"


def test_student_requires_approved_grant() -> None:
    handler = _build_handler()
    result = handler(
        CheckCourseAccessQuery(
            course_id="course-1",
            actor_account_id="student-2",
            actor_roles=["student"],
        )
    )

    assert result.decision == "deny"
    assert result.reason_code == "access_grant_required"

