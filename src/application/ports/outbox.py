"""Outbox port for reliable cross-service side effects."""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime
from enum import StrEnum
from typing import Protocol


class OutboxEventStatus(StrEnum):
    """Lifecycle status of a persisted outbox event."""

    PENDING = "pending"
    PROCESSED = "processed"


class OutboxEventType(StrEnum):
    """Known course_service outbox event types."""

    COURSE_COMPLETION_BONUS_ACCRUAL = "course_completion_bonus_accrual"


@dataclass(frozen=True, slots=True)
class OutboxEventRecord:
    """Persisted outbox event."""

    event_id: str
    aggregate_type: str
    aggregate_id: str
    event_type: OutboxEventType
    payload_json: str
    status: OutboxEventStatus
    attempt_count: int
    available_at: datetime
    created_at: datetime
    processed_at: datetime | None = None
    last_error: str | None = None

    def mark_processed(self, *, at: datetime) -> "OutboxEventRecord":
        return replace(
            self,
            status=OutboxEventStatus.PROCESSED,
            processed_at=at,
            last_error=None,
        )

    def mark_failed(self, *, error: str) -> "OutboxEventRecord":
        return replace(
            self,
            attempt_count=self.attempt_count + 1,
            last_error=error[:1000],
        )


class OutboxEventRepository(Protocol):
    """Persisted outbox storage."""

    def add(self, event: OutboxEventRecord) -> None:
        """Store a new outbox event."""

    def save(self, event: OutboxEventRecord) -> None:
        """Persist an updated outbox event state."""

    def list_pending(self, *, limit: int = 100) -> list[OutboxEventRecord]:
        """Return pending events ordered by creation time."""
