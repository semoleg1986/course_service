"""Общие DTO application-слоя."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class AccessDecisionResult:
    """Результат проверки доступа к курсу."""

    decision: str
    reason_code: str
    course_id: str
    actor_account_id: str
    student_id: str | None
    grant_status: str | None
    enrollment_status: str | None
    checked_at: datetime

