"""Порт retained audit evidence для course_service."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol


@dataclass(frozen=True, slots=True)
class AuditEvidenceRecord:
    """Append-only запись retained audit evidence."""

    audit_id: str
    action: str
    occurred_at: datetime
    result: str
    actor_id: str | None
    actor_roles: tuple[str, ...]
    target_type: str
    target_id: str | None
    reason: str | None = None
    reason_code: str | None = None
    request_id: str | None = None
    correlation_id: str | None = None
    course_id: str | None = None


class AuditEvidenceRepository(Protocol):
    """Контракт append-only хранилища retained audit evidence."""

    def append(self, record: AuditEvidenceRecord) -> None:
        """Сохраняет audit evidence запись."""
