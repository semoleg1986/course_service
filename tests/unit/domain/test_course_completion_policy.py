from datetime import UTC, datetime, timedelta

from src.domain.content.course.entity import Course, Lesson, Module
from src.domain.content.course.value_objects import (
    CourseSchedule,
    CourseSlug,
    SeoMetadata,
)
from src.domain.learning.course_progress.policy import CourseCompletionPolicy
from src.domain.shared.statuses import CourseProgressStatus


def _now() -> datetime:
    return datetime(2026, 5, 2, 12, 0, tzinfo=UTC)


def _published_module(
    *,
    module_id: str,
    lesson_ids: list[str],
    now: datetime,
    is_required: bool = True,
) -> Module:
    module = Module.create(
        module_id=module_id,
        title=f"Module {module_id}",
        created_at=now,
        created_by="teacher-1",
        is_required=is_required,
    )
    for lesson_id in lesson_ids:
        lesson = Lesson.create(
            lesson_id=lesson_id,
            title=f"Lesson {lesson_id}",
            created_at=now,
            created_by="teacher-1",
        )
        lesson.update(
            title=None,
            description=None,
            content_type=None,
            content_ref=None,
            duration_minutes=None,
            is_preview=None,
            released_at=None,
            status="published",
            changed_at=now,
            changed_by="teacher-1",
        )
        module.add_lesson(lesson, changed_at=now, changed_by="teacher-1")
    module.update(
        title=None,
        description=None,
        is_required=None,
        released_at=None,
        status="published",
        changed_at=now,
        changed_by="teacher-1",
    )
    return module


def _draft_module(*, module_id: str, lesson_ids: list[str], now: datetime) -> Module:
    module = Module.create(
        module_id=module_id,
        title=f"Draft {module_id}",
        created_at=now,
        created_by="teacher-1",
        is_required=True,
    )
    for lesson_id in lesson_ids:
        lesson = Lesson.create(
            lesson_id=lesson_id,
            title=f"Lesson {lesson_id}",
            created_at=now,
            created_by="teacher-1",
        )
        module.add_lesson(lesson, changed_at=now, changed_by="teacher-1")
    return module


def _course(now: datetime) -> Course:
    course = Course.create(
        course_id="course-1",
        title="Math",
        description="Math course",
        teacher_id="teacher-1",
        slug=CourseSlug("math"),
        schedule=CourseSchedule(starts_at=now, duration_days=30),
        seo=SeoMetadata(meta_title="Math", meta_description="Math course"),
        created_at=now,
        created_by="teacher-1",
    )
    return course


def test_completion_policy_uses_required_modules_only_when_present() -> None:
    now = _now()
    course = _course(now)
    course.add_module(
        _published_module(
            module_id="required-1",
            lesson_ids=["l-1", "l-2"],
            now=now,
            is_required=True,
        ),
        changed_at=now,
        changed_by="teacher-1",
    )
    course.add_module(
        _published_module(
            module_id="optional-1",
            lesson_ids=["l-3"],
            now=now,
            is_required=False,
        ),
        changed_at=now,
        changed_by="teacher-1",
    )

    summary = CourseCompletionPolicy.evaluate(
        course=course,
        completed_lesson_ids={"l-1", "l-2"},
        evaluated_at=now,
    )

    assert summary.required_lesson_ids == ("l-1", "l-2")
    assert summary.total_lessons == 2
    assert summary.completed_lessons == 2
    assert summary.status == CourseProgressStatus.COMPLETED
    assert summary.progress_percent == 100.0
    assert summary.completed_at == now


def test_completion_policy_falls_back_to_all_published_modules() -> None:
    now = _now()
    course = _course(now)
    course.add_module(
        _published_module(
            module_id="optional-1",
            lesson_ids=["l-1", "l-2"],
            now=now,
            is_required=False,
        ),
        changed_at=now,
        changed_by="teacher-1",
    )
    course.add_module(
        _published_module(
            module_id="optional-2",
            lesson_ids=["l-3"],
            now=now,
            is_required=False,
        ),
        changed_at=now,
        changed_by="teacher-1",
    )

    summary = CourseCompletionPolicy.evaluate(
        course=course,
        completed_lesson_ids={"l-1"},
        evaluated_at=now,
    )

    assert summary.required_lesson_ids == ("l-1", "l-2", "l-3")
    assert summary.total_lessons == 3
    assert summary.completed_lessons == 1
    assert summary.status == CourseProgressStatus.IN_PROGRESS
    assert summary.progress_percent == 33.33
    assert summary.completed_at is None


def test_completion_policy_ignores_draft_content_and_unknown_ids() -> None:
    now = _now()
    course = _course(now)
    course.add_module(
        _published_module(
            module_id="required-1",
            lesson_ids=["l-1"],
            now=now,
            is_required=True,
        ),
        changed_at=now,
        changed_by="teacher-1",
    )
    course.add_module(
        _draft_module(module_id="draft-1", lesson_ids=["l-draft"], now=now),
        changed_at=now,
        changed_by="teacher-1",
    )

    summary = CourseCompletionPolicy.evaluate(
        course=course,
        completed_lesson_ids=["l-1", "l-1", "l-draft", "unknown"],
        evaluated_at=now,
    )

    assert summary.required_lesson_ids == ("l-1",)
    assert summary.completed_lesson_ids == ("l-1",)
    assert summary.completed_lessons == 1
    assert summary.total_lessons == 1


def test_completion_policy_reports_not_started_when_nothing_completed() -> None:
    now = _now()
    course = _course(now)
    course.add_module(
        _published_module(
            module_id="required-1",
            lesson_ids=["l-1", "l-2"],
            now=now,
            is_required=True,
        ),
        changed_at=now,
        changed_by="teacher-1",
    )

    summary = CourseCompletionPolicy.evaluate(
        course=course,
        completed_lesson_ids=set(),
        evaluated_at=now + timedelta(minutes=10),
    )

    assert summary.status == CourseProgressStatus.NOT_STARTED
    assert summary.progress_percent == 0.0
    assert summary.completed_at is None
