"""In-memory persisted outbox storage."""

from __future__ import annotations

from src.application.ports.outbox import OutboxEventRecord, OutboxEventStatus


class InMemoryOutboxRepository:
    """Simple in-memory outbox storage for tests and local runtime."""

    def __init__(self) -> None:
        self._items: dict[str, OutboxEventRecord] = {}

    def add(self, event: OutboxEventRecord) -> None:
        self._items[event.event_id] = event

    def save(self, event: OutboxEventRecord) -> None:
        self._items[event.event_id] = event

    def list_pending(self, *, limit: int = 100) -> list[OutboxEventRecord]:
        return sorted(
            (
                item
                for item in self._items.values()
                if item.status == OutboxEventStatus.PENDING
            ),
            key=lambda item: item.created_at,
        )[:limit]
