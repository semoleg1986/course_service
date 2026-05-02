from __future__ import annotations

from dataclasses import replace
from datetime import datetime

from src.application.ports.access_read_model import AccessReadModel
from src.domain.content.course.entity import Course
from src.domain.learning.course_progress.policy import (
    CourseCompletionPolicy,
    CourseProgressSummary,
)
from src.domain.shared.statuses import CourseProgressStatus


def evaluate_course_progress_summary(
    *,
    course: Course,
    student_id: str,
    read_model: AccessReadModel,
    evaluated_at: datetime,
) -> CourseProgressSummary:
    """Считает summary курса и нормализует completed_at по реальным lesson progress."""

    summary = CourseCompletionPolicy.evaluate(
        course=course,
        completed_lesson_ids=read_model.list_completed_lesson_ids(
            course_id=course.course_id,
            student_id=student_id,
        ),
        evaluated_at=evaluated_at,
    )
    if summary.status != CourseProgressStatus.COMPLETED:
        return summary

    completed_timestamps = []
    for lesson_id in summary.completed_lesson_ids:
        payload = read_model.get_lesson_progress(
            course_id=course.course_id,
            student_id=student_id,
            lesson_id=lesson_id,
        )
        if payload is None:
            continue
        completed_at = payload.get("completed_at")
        if isinstance(completed_at, datetime):
            completed_timestamps.append(completed_at)

    if not completed_timestamps:
        return summary
    return replace(summary, completed_at=max(completed_timestamps))
