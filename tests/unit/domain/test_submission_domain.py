from datetime import UTC, datetime

import pytest

from src.domain.errors import InvariantViolationError
from src.domain.evaluation.submission.entity import Submission


def test_submission_lifecycle_started_submitted_graded() -> None:
    now = datetime(2026, 4, 9, tzinfo=UTC)
    submission = Submission.create(
        submission_id="sub-1",
        enrollment_id="enr-1",
        created_at=now,
        created_by="student-1",
    )

    submission.submit(changed_at=now, changed_by="student-1")
    assert submission.status.value == "submitted"

    submission.grade(score=95, feedback="good", changed_at=now, changed_by="teacher-1")
    assert submission.status.value == "graded"
    assert submission.score == 95


def test_submission_guards_on_invalid_transitions() -> None:
    now = datetime(2026, 4, 9, tzinfo=UTC)
    submission = Submission.create(
        submission_id="sub-1",
        enrollment_id="enr-1",
        created_at=now,
        created_by="student-1",
    )

    with pytest.raises(InvariantViolationError):
        submission.grade(score=90, feedback=None, changed_at=now, changed_by="teacher-1")

    submission.submit(changed_at=now, changed_by="student-1")
    with pytest.raises(InvariantViolationError):
        submission.submit(changed_at=now, changed_by="student-1")

    with pytest.raises(InvariantViolationError):
        submission.grade(score=-1, feedback=None, changed_at=now, changed_by="teacher-1")
