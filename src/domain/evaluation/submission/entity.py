from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from src.domain.errors import InvariantViolationError
from src.domain.shared.entity import EntityMeta
from src.domain.shared.statuses import SubmissionStatus


@dataclass(slots=True)
class Submission:
    """
    Aggregate Root попытки/сдачи задания.

    :param submission_id: Идентификатор сдачи.
    :type submission_id: str
    :param enrollment_id: Идентификатор enrollment.
    :type enrollment_id: str
    """

    submission_id: str
    enrollment_id: str
    meta: EntityMeta
    status: SubmissionStatus = SubmissionStatus.STARTED
    score: float | None = None
    feedback: str | None = None

    @classmethod
    def create(
        cls,
        submission_id: str,
        enrollment_id: str,
        created_at: datetime,
        created_by: str,
    ) -> "Submission":
        """Создать новую сдачу."""
        return cls(
            submission_id=submission_id,
            enrollment_id=enrollment_id,
            meta=EntityMeta.create(at=created_at, actor_id=created_by),
            status=SubmissionStatus.STARTED,
        )

    def submit(self, changed_at: datetime, changed_by: str) -> None:
        """Перевести сдачу в состояние submitted."""
        if self.status != SubmissionStatus.STARTED:
            raise InvariantViolationError("Сдачу можно отправить только из состояния started")
        self.status = SubmissionStatus.SUBMITTED
        self.meta.touch(at=changed_at, actor_id=changed_by)

    def grade(
        self,
        score: float,
        feedback: str | None,
        changed_at: datetime,
        changed_by: str,
    ) -> None:
        """
        Оценить отправленную сдачу.

        :raises InvariantViolationError: Если нарушен жизненный цикл submission.
        """
        if self.status != SubmissionStatus.SUBMITTED:
            raise InvariantViolationError("Оценивание возможно только для submitted-сдачи")
        if score < 0:
            raise InvariantViolationError("Оценка не может быть отрицательной")
        self.status = SubmissionStatus.GRADED
        self.score = score
        self.feedback = feedback
        self.meta.touch(at=changed_at, actor_id=changed_by)
