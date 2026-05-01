"""Handlers parent read API по прогрессу ученика."""

from __future__ import annotations

from src.application.access.queries.dto import (
    ListParentStudentCompletedCoursesQuery,
    ListParentStudentCourseProgressQuery,
)
from src.application.common.dto import (
    CompletedCourseItemResult,
    CourseProgressItemResult,
)
from src.application.ports.access_read_model import AccessReadModel
from src.application.ports.clock import Clock
from src.application.ports.parent_student_relation_checker import (
    ParentStudentRelationChecker,
)
from src.domain.content.course.repository import CourseRepository
from src.domain.errors import AccessDeniedError
from src.domain.shared.statuses import EnrollmentStatus


def _compute_progress(
    *,
    enrollment_status: str | None,
    total_lessons: int,
) -> tuple[float, int]:
    if total_lessons <= 0:
        return (
            100.0 if enrollment_status == EnrollmentStatus.COMPLETED.value else 0.0,
            0,
        )
    if enrollment_status == EnrollmentStatus.COMPLETED.value:
        return (100.0, total_lessons)
    return (0.0, 0)


class ListParentStudentCourseProgressHandler:
    """Возвращает список прогресса ученика по курсам."""

    def __init__(
        self,
        *,
        read_model: AccessReadModel,
        course_repository: CourseRepository,
        relation_checker: ParentStudentRelationChecker,
    ) -> None:
        self._read_model = read_model
        self._course_repository = course_repository
        self._relation_checker = relation_checker

    def __call__(
        self, query: ListParentStudentCourseProgressQuery
    ) -> list[CourseProgressItemResult]:
        role_set = {role.strip().lower() for role in query.actor_roles}
        if "parent" not in role_set and "admin" not in role_set:
            raise AccessDeniedError("Операция доступна parent или admin.")

        if "admin" not in role_set and not self._relation_checker.has_relation(
            parent_id=query.actor_id,
            student_id=query.student_id,
        ):
            raise AccessDeniedError("Нет доступа к данным ученика.")

        grants = self._read_model.list_access_grants_by_student(query.student_id)
        enrollment_map = dict(
            self._read_model.list_enrollments_by_student(query.student_id)
        )
        items: list[CourseProgressItemResult] = []
        for course_id, grant_status in grants:
            enrollment_status = enrollment_map.get(course_id)
            effective_status = enrollment_status or grant_status
            if query.status and effective_status != query.status:
                continue

            course = self._course_repository.get(course_id)

            total_lessons = course.lessons_total if course is not None else 0
            progress_percent, completed_lessons = _compute_progress(
                enrollment_status=enrollment_status,
                total_lessons=total_lessons,
            )
            items.append(
                CourseProgressItemResult(
                    course_id=course_id,
                    title=course.title if course is not None else course_id,
                    progress_percent=progress_percent,
                    completed_lessons=completed_lessons,
                    total_lessons=total_lessons,
                    status=effective_status,
                )
            )
        items.sort(key=lambda item: item.course_id)
        return items[query.offset : query.offset + query.limit]


class ListParentStudentCompletedCoursesHandler:
    """Возвращает список завершенных курсов ученика."""

    def __init__(
        self,
        *,
        read_model: AccessReadModel,
        course_repository: CourseRepository,
        relation_checker: ParentStudentRelationChecker,
        clock: Clock,
    ) -> None:
        self._read_model = read_model
        self._course_repository = course_repository
        self._relation_checker = relation_checker
        self._clock = clock

    def __call__(
        self, query: ListParentStudentCompletedCoursesQuery
    ) -> list[CompletedCourseItemResult]:
        role_set = {role.strip().lower() for role in query.actor_roles}
        if "parent" not in role_set and "admin" not in role_set:
            raise AccessDeniedError("Операция доступна parent или admin.")

        if "admin" not in role_set and not self._relation_checker.has_relation(
            parent_id=query.actor_id,
            student_id=query.student_id,
        ):
            raise AccessDeniedError("Нет доступа к данным ученика.")

        enrollments = self._read_model.list_enrollments_by_student(query.student_id)
        completed_course_ids = sorted(
            [
                course_id
                for course_id, status in enrollments
                if status == EnrollmentStatus.COMPLETED.value
            ]
        )
        items: list[CompletedCourseItemResult] = []
        for course_id in completed_course_ids:
            course = self._course_repository.get(course_id)
            items.append(
                CompletedCourseItemResult(
                    course_id=course_id,
                    title=course.title if course is not None else course_id,
                    # Отдельного timestamp completion пока нет в projection,
                    # поэтому отдаем timestamp формирования ответа.
                    completed_at=self._clock.now(),
                )
            )

        return items[query.offset : query.offset + query.limit]
