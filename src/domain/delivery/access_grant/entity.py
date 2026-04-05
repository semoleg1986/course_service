from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from src.domain.errors import InvariantViolationError
from src.domain.shared.entity import EntityMeta
from src.domain.shared.statuses import AccessGrantStatus
from .value_objects import AttributionSnapshot, PaymentConfirmation


@dataclass(slots=True)
class AccessGrant:
    """
    Aggregate Root доступа ученика к курсу.

    :param grant_id: Идентификатор grant.
    :type grant_id: str
    :param course_id: Идентификатор курса.
    :type course_id: str
    :param student_id: Идентификатор ученика.
    :type student_id: str
    """

    grant_id: str
    course_id: str
    student_id: str
    meta: EntityMeta
    status: AccessGrantStatus = AccessGrantStatus.REQUESTED
    attribution: AttributionSnapshot | None = None
    requested_at: datetime | None = None
    payment: PaymentConfirmation | None = None
    approved_by_admin_id: str | None = None

    @classmethod
    def request(
        cls,
        grant_id: str,
        course_id: str,
        student_id: str,
        requested_at: datetime,
        requested_by: str,
        attribution: AttributionSnapshot | None = None,
    ) -> "AccessGrant":
        """Создать новый запрос доступа к курсу."""
        return cls(
            grant_id=grant_id,
            course_id=course_id,
            student_id=student_id,
            meta=EntityMeta.create(at=requested_at, actor_id=requested_by),
            status=AccessGrantStatus.REQUESTED,
            attribution=attribution,
            requested_at=requested_at,
        )

    def mark_paid(
        self,
        payment: PaymentConfirmation,
        changed_at: datetime,
        changed_by: str,
    ) -> None:
        """
        Зафиксировать оплату запроса доступа.

        :raises InvariantViolationError: Если статус не допускает оплату.
        """
        if self.status not in {AccessGrantStatus.REQUESTED, AccessGrantStatus.PAID}:
            raise InvariantViolationError("Оплату можно отметить только для запрошенного доступа")
        self.payment = payment
        self.status = AccessGrantStatus.PAID
        self.meta.touch(at=changed_at, actor_id=changed_by)

    def approve(self, admin_id: str, changed_at: datetime) -> None:
        """
        Одобрить доступ к курсу.

        :raises InvariantViolationError: Если доступ не в статусе paid.
        """
        if self.status != AccessGrantStatus.PAID:
            raise InvariantViolationError("Доступ можно одобрить только из статуса paid")
        self.status = AccessGrantStatus.APPROVED
        self.approved_by_admin_id = admin_id
        self.meta.touch(at=changed_at, actor_id=admin_id)

    def reject(self, changed_at: datetime, changed_by: str) -> None:
        """Отклонить запрос доступа."""
        if self.status in {AccessGrantStatus.APPROVED, AccessGrantStatus.REVOKED}:
            raise InvariantViolationError("Одобренный/отозванный доступ нельзя отклонить")
        self.status = AccessGrantStatus.REJECTED
        self.meta.touch(at=changed_at, actor_id=changed_by)

    def revoke(self, changed_at: datetime, changed_by: str) -> None:
        """Отозвать ранее одобренный доступ."""
        if self.status != AccessGrantStatus.APPROVED:
            raise InvariantViolationError("Отозвать можно только одобренный доступ")
        self.status = AccessGrantStatus.REVOKED
        self.meta.touch(at=changed_at, actor_id=changed_by)

    @property
    def is_enrollment_allowed(self) -> bool:
        """Признак, что по grant можно создавать enrollment."""
        return self.status == AccessGrantStatus.APPROVED
