from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from src.domain.content.course.entity import Course
from src.domain.delivery.access_grant.entity import AccessGrant
from src.domain.errors import InvariantViolationError
from src.domain.shared.entity import EntityMeta
from src.domain.shared.statuses import EnrollmentStatus, PublishState


@dataclass(slots=True)
class Enrollment:
    """
    Aggregate Root записи ученика на курс.

    :param enrollment_id: Идентификатор записи.
    :type enrollment_id: str
    :param course_id: Идентификатор курса.
    :type course_id: str
    :param student_id: Идентификатор ученика.
    :type student_id: str
    """

    enrollment_id: str
    course_id: str
    student_id: str
    meta: EntityMeta
    status: EnrollmentStatus = EnrollmentStatus.ACTIVE

    @classmethod
    def create(
        cls,
        enrollment_id: str,
        course: Course,
        grant: AccessGrant,
        student_id: str,
        created_at: datetime,
        created_by: str,
    ) -> "Enrollment":
        """
        Создать запись на курс.

        :raises InvariantViolationError: Если курс/доступ не удовлетворяют инвариантам.
        """
        if course.publish_state != PublishState.PUBLISHED:
            raise InvariantViolationError("Запись возможна только на опубликованный курс")
        if grant.student_id != student_id or grant.course_id != course.course_id:
            raise InvariantViolationError("AccessGrant не соответствует ученику/курсу")
        if not grant.is_enrollment_allowed:
            raise InvariantViolationError("Для записи требуется одобренный доступ")
        return cls(
            enrollment_id=enrollment_id,
            course_id=course.course_id,
            student_id=student_id,
            meta=EntityMeta.create(at=created_at, actor_id=created_by),
            status=EnrollmentStatus.ACTIVE,
        )

    def complete(self, changed_at: datetime, changed_by: str) -> None:
        """Отметить курс как завершенный для enrollment."""
        self.status = EnrollmentStatus.COMPLETED
        self.meta.touch(at=changed_at, actor_id=changed_by)
