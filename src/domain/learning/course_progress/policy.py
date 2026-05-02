from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from src.domain.content.course.entity import Course, Lesson, Module
from src.domain.shared.statuses import CourseProgressStatus, PublishState


@dataclass(frozen=True, slots=True)
class CourseProgressSummary:
    """Результат вычисления прогресса ученика по курсу."""

    course_id: str
    status: CourseProgressStatus
    progress_percent: float
    completed_lessons: int
    total_lessons: int
    required_lesson_ids: tuple[str, ...]
    completed_lesson_ids: tuple[str, ...]
    completed_at: datetime | None


class CourseCompletionPolicy:
    """
    Правила завершения курса.

    Текущие правила Sprint 3:
    - учитываются только `published` модули и `published` уроки;
    - если в курсе есть published required-модули с published уроками,
      курс завершается по всем урокам из этих required-модулей;
    - если required-модулей нет, считаются все published уроки курса;
    - неизвестные lesson_id и дубликаты в completed set игнорируются.
    """

    @classmethod
    def evaluate(
        cls,
        *,
        course: Course,
        completed_lesson_ids: set[str] | list[str] | tuple[str, ...],
        evaluated_at: datetime,
    ) -> CourseProgressSummary:
        eligible_modules = cls._published_modules(course)
        required_modules = [
            module
            for module in eligible_modules
            if module.is_required and cls._published_lessons(module)
        ]
        modules_for_completion = required_modules or eligible_modules

        required_lessons = [
            lesson
            for module in modules_for_completion
            for lesson in cls._published_lessons(module)
        ]
        required_lesson_ids = tuple(lesson.lesson_id for lesson in required_lessons)
        required_set = set(required_lesson_ids)

        completed_unique = tuple(
            lesson_id
            for lesson_id in dict.fromkeys(completed_lesson_ids)
            if lesson_id in required_set
        )
        completed_count = len(completed_unique)
        total_count = len(required_lesson_ids)

        if total_count == 0 or completed_count == 0:
            status = CourseProgressStatus.NOT_STARTED
        elif completed_count < total_count:
            status = CourseProgressStatus.IN_PROGRESS
        else:
            status = CourseProgressStatus.COMPLETED

        percent = 0.0
        if total_count > 0:
            percent = round((completed_count / total_count) * 100, 2)

        return CourseProgressSummary(
            course_id=course.course_id,
            status=status,
            progress_percent=percent,
            completed_lessons=completed_count,
            total_lessons=total_count,
            required_lesson_ids=required_lesson_ids,
            completed_lesson_ids=completed_unique,
            completed_at=(
                evaluated_at if status == CourseProgressStatus.COMPLETED else None
            ),
        )

    @staticmethod
    def _published_modules(course: Course) -> list[Module]:
        return [
            module
            for module in course.modules
            if module.status == PublishState.PUBLISHED
        ]

    @staticmethod
    def _published_lessons(module: Module) -> list[Lesson]:
        return [
            lesson
            for lesson in module.lessons
            if lesson.status == PublishState.PUBLISHED
        ]
