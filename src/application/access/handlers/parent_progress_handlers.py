"""Handlers parent read API по прогрессу ученика."""

from __future__ import annotations

from datetime import datetime

from src.application.access.queries.dto import (
    ListParentStudentCompletedCoursesQuery,
    ListParentStudentCourseProgressQuery,
)
from src.application.common.dto import (
    CompletedCourseItemResult,
    CourseProgressItemResult,
)
from src.application.learning.progress_summary import (
    evaluate_course_progress_summary,
)
from src.application.ports.access_read_model import AccessReadModel
from src.application.ports.clock import Clock
from src.application.ports.parent_student_relation_checker import (
    ParentStudentRelationChecker,
)
from src.domain.content.course.repository import CourseRepository
from src.domain.errors import AccessDeniedError
from src.domain.shared.statuses import CourseProgressStatus


def _candidate_course_ids(*, read_model: AccessReadModel, student_id: str) -> list[str]:
    grant_ids = {
        course_id
        for course_id, _status in read_model.list_access_grants_by_student(student_id)
    }
    enrollment_ids = {
        course_id
        for course_id, _status in read_model.list_enrollments_by_student(student_id)
    }
    return sorted(grant_ids | enrollment_ids)


def _get_or_compute_summary(
    *,
    read_model: AccessReadModel,
    course_repository: CourseRepository,
    clock: Clock,
    course_id: str,
    student_id: str,
) -> tuple[str, float, int, int, datetime | None]:
    existing = read_model.get_course_progress_summary(
        course_id=course_id,
        student_id=student_id,
    )
    if existing is not None:
        return existing

    course = course_repository.get(course_id)
    if course is None:
        return (
            CourseProgressStatus.NOT_STARTED.value,
            0.0,
            0,
            0,
            None,
        )

    computed = evaluate_course_progress_summary(
        course=course,
        student_id=student_id,
        read_model=read_model,
        evaluated_at=clock.now(),
    )
    read_model.store_course_progress_summary(
        course_id=course_id,
        student_id=student_id,
        status=computed.status.value,
        progress_percent=computed.progress_percent,
        completed_lessons=computed.completed_lessons,
        total_lessons=computed.total_lessons,
        completed_at=computed.completed_at,
    )
    return (
        computed.status.value,
        computed.progress_percent,
        computed.completed_lessons,
        computed.total_lessons,
        computed.completed_at,
    )


class ListParentStudentCourseProgressHandler:
    """Возвращает список прогресса ученика по курсам."""

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

        items: list[CourseProgressItemResult] = []
        for course_id in _candidate_course_ids(
            read_model=self._read_model,
            student_id=query.student_id,
        ):
            (
                status,
                progress_percent,
                completed_lessons,
                total_lessons,
                _completed_at,
            ) = _get_or_compute_summary(
                read_model=self._read_model,
                course_repository=self._course_repository,
                clock=self._clock,
                course_id=course_id,
                student_id=query.student_id,
            )
            if query.status and status != query.status:
                continue

            course = self._course_repository.get(course_id)
            items.append(
                CourseProgressItemResult(
                    course_id=course_id,
                    title=course.title if course is not None else course_id,
                    progress_percent=progress_percent,
                    completed_lessons=completed_lessons,
                    total_lessons=total_lessons,
                    status=status,
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

        items: list[CompletedCourseItemResult] = []
        for course_id in _candidate_course_ids(
            read_model=self._read_model,
            student_id=query.student_id,
        ):
            (
                status,
                _progress_percent,
                _completed_lessons,
                _total_lessons,
                completed_at,
            ) = _get_or_compute_summary(
                read_model=self._read_model,
                course_repository=self._course_repository,
                clock=self._clock,
                course_id=course_id,
                student_id=query.student_id,
            )
            if status != CourseProgressStatus.COMPLETED.value or completed_at is None:
                continue
            course = self._course_repository.get(course_id)
            items.append(
                CompletedCourseItemResult(
                    course_id=course_id,
                    title=course.title if course is not None else course_id,
                    completed_at=completed_at,
                )
            )

        return items[query.offset : query.offset + query.limit]
