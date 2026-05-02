from __future__ import annotations

from uuid import uuid4

from src.application.access.queries.dto import CheckCourseAccessQuery
from src.application.common.dto import StudentLessonCompletionResult
from src.application.learning.commands.dto import CompleteLessonCommand
from src.application.ports.access_read_model import AccessReadModel
from src.application.ports.clock import Clock
from src.domain.content.course.entity import Course, Lesson, Module
from src.domain.content.course.repository import CourseRepository
from src.domain.errors import AccessDeniedError, NotFoundError
from src.domain.learning.course_progress.policy import CourseCompletionPolicy
from src.domain.learning.lesson_progress.entity import LessonProgress
from src.domain.shared.statuses import LessonProgressStatus


class CompleteLessonHandler:
    """Отмечает урок завершенным и пересчитывает course progress."""

    def __init__(
        self,
        *,
        course_repository: CourseRepository,
        read_model: AccessReadModel,
        clock: Clock,
        check_access_handler,
    ) -> None:
        self._course_repository = course_repository
        self._read_model = read_model
        self._clock = clock
        self._check_access_handler = check_access_handler

    def __call__(self, command: CompleteLessonCommand) -> StudentLessonCompletionResult:
        role_set = {
            role.strip().lower() for role in command.actor_roles if role.strip()
        }
        if "student" not in role_set:
            raise AccessDeniedError("Операция доступна только student.")

        course = self._course_repository.get(command.course_id)
        if course is None:
            raise NotFoundError("Курс не найден.")

        module, lesson = self._find_published_lesson(course, command.lesson_id)
        if module is None or lesson is None:
            raise NotFoundError("Урок не найден или недоступен для прохождения.")

        decision = self._check_access_handler(
            CheckCourseAccessQuery(
                course_id=command.course_id,
                actor_account_id=command.actor_id,
                actor_roles=command.actor_roles,
                student_id=command.actor_id,
                require_active_grant=True,
                require_enrollment=False,
            )
        )
        if decision.decision != "allow":
            raise AccessDeniedError("Нет активного доступа к курсу.")

        now = self._clock.now()
        existing = self._read_model.get_lesson_progress(
            course_id=command.course_id,
            student_id=command.actor_id,
            lesson_id=command.lesson_id,
        )
        if existing is None:
            progress = LessonProgress.create(
                progress_id=str(uuid4()),
                course_id=command.course_id,
                module_id=module.module_id,
                lesson_id=command.lesson_id,
                student_id=command.actor_id,
                created_at=now,
                created_by=command.actor_id,
            )
        else:
            progress = LessonProgress.restore(
                progress_id=str(existing["progress_id"]),
                course_id=command.course_id,
                module_id=module.module_id,
                lesson_id=command.lesson_id,
                student_id=command.actor_id,
                status=LessonProgressStatus(str(existing["status"])),
                created_at=existing["created_at"],
                created_by=str(existing["created_by"]),
                updated_at=existing["updated_at"],
                updated_by=str(existing["updated_by"]),
                version=int(existing["version"]),
                started_at=existing["started_at"],
                completed_at=existing["completed_at"],
                last_activity_at=existing["last_activity_at"],
            )

        progress.complete(changed_at=now, changed_by=command.actor_id)
        self._read_model.upsert_lesson_progress(
            course_id=progress.course_id,
            module_id=progress.module_id,
            lesson_id=progress.lesson_id,
            student_id=progress.student_id,
            progress_id=progress.progress_id,
            status=progress.status.value,
            created_at=progress.meta.created_at,
            created_by=progress.meta.created_by,
            updated_at=progress.meta.updated_at,
            updated_by=progress.meta.updated_by,
            version=progress.meta.version,
            started_at=progress.started_at,
            completed_at=progress.completed_at,
            last_activity_at=progress.last_activity_at,
        )

        summary = CourseCompletionPolicy.evaluate(
            course=course,
            completed_lesson_ids=self._read_model.list_completed_lesson_ids(
                course_id=command.course_id,
                student_id=command.actor_id,
            ),
            evaluated_at=now,
        )
        self._read_model.store_course_progress_summary(
            course_id=command.course_id,
            student_id=command.actor_id,
            status=summary.status.value,
            progress_percent=summary.progress_percent,
            completed_lessons=summary.completed_lessons,
            total_lessons=summary.total_lessons,
            completed_at=summary.completed_at,
        )
        return StudentLessonCompletionResult(
            course_id=command.course_id,
            module_id=module.module_id,
            lesson_id=command.lesson_id,
            student_id=command.actor_id,
            lesson_status=progress.status.value,
            course_status=summary.status.value,
            progress_percent=summary.progress_percent,
            completed_lessons=summary.completed_lessons,
            total_lessons=summary.total_lessons,
            completed_at=summary.completed_at,
        )

    @staticmethod
    def _find_published_lesson(
        course: Course, lesson_id: str
    ) -> tuple[Module | None, Lesson | None]:
        for module in course.modules:
            if module.status.value != "published":
                continue
            for lesson in module.lessons:
                if lesson.lesson_id == lesson_id and lesson.status.value == "published":
                    return module, lesson
        return None, None
