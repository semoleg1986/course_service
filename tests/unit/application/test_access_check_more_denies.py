from __future__ import annotations

from src.application.access.handlers.check_course_access_handler import CheckCourseAccessHandler
from src.application.access.queries.dto import CheckCourseAccessQuery
from src.infrastructure.clock.system_clock import SystemClock
from src.infrastructure.db.inmemory.access_read_model import InMemoryAccessReadModel


def test_denies_not_approved_grant_and_enrollment_branches() -> None:
    read_model = InMemoryAccessReadModel()
    read_model.seed_course_owner("course-1", "teacher-1")
    read_model.seed_access_grant_status("course-1", "student-1", "paid")
    handler = CheckCourseAccessHandler(read_model=read_model, clock=SystemClock())

    not_approved = handler(
        CheckCourseAccessQuery(
            course_id="course-1",
            actor_account_id="student-1",
            actor_roles=["student"],
            student_id="student-1",
            require_active_grant=True,
            require_enrollment=True,
        )
    )
    assert not_approved.reason_code == "access_grant_not_approved"

    read_model.seed_access_grant_status("course-1", "student-1", "approved")
    enrollment_missing = handler(
        CheckCourseAccessQuery(
            course_id="course-1",
            actor_account_id="student-1",
            actor_roles=["student"],
            student_id="student-1",
            require_active_grant=True,
            require_enrollment=True,
        )
    )
    assert enrollment_missing.reason_code == "enrollment_required"

    read_model.seed_enrollment_status("course-1", "student-1", "completed")
    enrollment_not_active = handler(
        CheckCourseAccessQuery(
            course_id="course-1",
            actor_account_id="student-1",
            actor_roles=["student"],
            student_id="student-1",
            require_active_grant=True,
            require_enrollment=True,
        )
    )
    assert enrollment_not_active.reason_code == "enrollment_not_active"
