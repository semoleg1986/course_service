from datetime import UTC, datetime, timedelta

import pytest

from src.domain.errors import InvariantViolationError
from src.domain.learning.lesson_progress.entity import LessonProgress
from src.domain.shared.statuses import LessonProgressStatus


def _now() -> datetime:
    return datetime(2026, 5, 2, 12, 0, tzinfo=UTC)


def test_lesson_progress_starts_from_not_started() -> None:
    now = _now()
    progress = LessonProgress.create(
        progress_id="lp-1",
        course_id="course-1",
        module_id="module-1",
        lesson_id="lesson-1",
        student_id="student-1",
        created_at=now,
        created_by="student-1",
    )

    assert progress.status == LessonProgressStatus.NOT_STARTED
    assert progress.started_at is None
    assert progress.completed_at is None
    assert progress.last_activity_at is None
    assert progress.meta.version == 1


def test_lesson_progress_start_sets_started_and_activity_timestamps() -> None:
    now = _now()
    progress = LessonProgress.create(
        progress_id="lp-1",
        course_id="course-1",
        module_id="module-1",
        lesson_id="lesson-1",
        student_id="student-1",
        created_at=now,
        created_by="student-1",
    )

    changed_at = now + timedelta(minutes=5)
    progress.start(changed_at=changed_at, changed_by="student-1")

    assert progress.status == LessonProgressStatus.IN_PROGRESS
    assert progress.started_at == changed_at
    assert progress.last_activity_at == changed_at
    assert progress.completed_at is None
    assert progress.meta.version == 2


def test_lesson_progress_complete_is_idempotent() -> None:
    now = _now()
    progress = LessonProgress.create(
        progress_id="lp-1",
        course_id="course-1",
        module_id="module-1",
        lesson_id="lesson-1",
        student_id="student-1",
        created_at=now,
        created_by="student-1",
    )

    completed_at = now + timedelta(minutes=20)
    progress.complete(changed_at=completed_at, changed_by="student-1")
    first_version = progress.meta.version

    assert progress.status == LessonProgressStatus.COMPLETED
    assert progress.started_at == completed_at
    assert progress.completed_at == completed_at
    assert progress.last_activity_at == completed_at

    progress.complete(
        changed_at=completed_at + timedelta(minutes=1),
        changed_by="student-1",
    )
    assert progress.meta.version == first_version
    assert progress.completed_at == completed_at


def test_lesson_progress_activity_promotes_not_started_and_blocks_completed() -> None:
    now = _now()
    progress = LessonProgress.create(
        progress_id="lp-1",
        course_id="course-1",
        module_id="module-1",
        lesson_id="lesson-1",
        student_id="student-1",
        created_at=now,
        created_by="student-1",
    )

    active_at = now + timedelta(minutes=3)
    progress.mark_activity(changed_at=active_at, changed_by="student-1")
    assert progress.status == LessonProgressStatus.IN_PROGRESS
    assert progress.started_at == active_at

    progress.complete(
        changed_at=active_at + timedelta(minutes=2),
        changed_by="student-1",
    )

    with pytest.raises(InvariantViolationError):
        progress.mark_activity(
            changed_at=active_at + timedelta(minutes=3),
            changed_by="student-1",
        )


def test_lesson_progress_validates_identifiers() -> None:
    now = _now()
    with pytest.raises(InvariantViolationError):
        LessonProgress.create(
            progress_id=" ",
            course_id="course-1",
            module_id="module-1",
            lesson_id="lesson-1",
            student_id="student-1",
            created_at=now,
            created_by="student-1",
        )
