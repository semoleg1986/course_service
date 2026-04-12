"""Handler проверки доступа к курсу."""

from __future__ import annotations

from src.application.access.queries.dto import CheckCourseAccessQuery
from src.application.common.dto import AccessDecisionResult
from src.application.ports.access_read_model import AccessReadModel
from src.application.ports.clock import Clock


class CheckCourseAccessHandler:
    """Проверяет доступ актора к курсу по ролям и состояниям доменных объектов."""

    def __init__(self, *, read_model: AccessReadModel, clock: Clock) -> None:
        self._read_model = read_model
        self._clock = clock

    def __call__(self, query: CheckCourseAccessQuery) -> AccessDecisionResult:
        owner_id = self._read_model.get_course_owner(query.course_id)
        if owner_id is None:
            return self._deny(query, "course_not_found")

        roles = set(query.actor_roles)
        if "admin" in roles:
            return self._allow(query, "admin_override")

        if "teacher" in roles and owner_id == query.actor_account_id:
            return self._allow(query, "teacher_owner")

        if "parent" not in roles and "student" not in roles:
            return self._deny(query, "role_not_allowed")

        student_id = query.student_id or query.actor_account_id
        grant_status = None
        if query.require_active_grant:
            grant_status = self._read_model.get_access_grant_status(
                query.course_id, student_id
            )
            if grant_status is None:
                return self._deny(query, "access_grant_required", student_id=student_id)
            if grant_status != "approved":
                return self._deny(
                    query,
                    "access_grant_not_approved",
                    student_id=student_id,
                    grant_status=grant_status,
                )

        enrollment_status = None
        if query.require_enrollment:
            enrollment_status = self._read_model.get_enrollment_status(
                query.course_id, student_id
            )
            if enrollment_status is None:
                return self._deny(
                    query,
                    "enrollment_required",
                    student_id=student_id,
                    grant_status=grant_status,
                )
            if enrollment_status != "active":
                return self._deny(
                    query,
                    "enrollment_not_active",
                    student_id=student_id,
                    grant_status=grant_status,
                    enrollment_status=enrollment_status,
                )

        reason = "parent_allowed" if "parent" in roles else "student_allowed"
        return self._allow(
            query,
            reason,
            student_id=student_id,
            grant_status=grant_status,
            enrollment_status=enrollment_status,
        )

    def _allow(
        self,
        query: CheckCourseAccessQuery,
        reason_code: str,
        *,
        student_id: str | None = None,
        grant_status: str | None = None,
        enrollment_status: str | None = None,
    ) -> AccessDecisionResult:
        return AccessDecisionResult(
            decision="allow",
            reason_code=reason_code,
            course_id=query.course_id,
            actor_account_id=query.actor_account_id,
            student_id=student_id,
            grant_status=grant_status,
            enrollment_status=enrollment_status,
            checked_at=self._clock.now(),
        )

    def _deny(
        self,
        query: CheckCourseAccessQuery,
        reason_code: str,
        *,
        student_id: str | None = None,
        grant_status: str | None = None,
        enrollment_status: str | None = None,
    ) -> AccessDecisionResult:
        return AccessDecisionResult(
            decision="deny",
            reason_code=reason_code,
            course_id=query.course_id,
            actor_account_id=query.actor_account_id,
            student_id=student_id,
            grant_status=grant_status,
            enrollment_status=enrollment_status,
            checked_at=self._clock.now(),
        )
