"""SQLAlchemy repository for persisted outbox events."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from src.application.ports.outbox import (
    OutboxEventRecord,
    OutboxEventStatus,
    OutboxEventType,
)
from src.infrastructure.db.sqlalchemy.models import CourseOutboxEventModel
from src.infrastructure.db.sqlalchemy.session import managed_session


class SqlalchemyOutboxRepository:
    """Persisted outbox storage on top of SQLAlchemy."""

    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    def add(self, event: OutboxEventRecord) -> None:
        with managed_session(self._session_factory) as db:
            db.add(self._to_model(event))

    def save(self, event: OutboxEventRecord) -> None:
        with managed_session(self._session_factory) as db:
            model = db.get(CourseOutboxEventModel, event.event_id)
            if model is None:
                db.add(self._to_model(event))
                return
            self._fill_model(model, event)

    def list_pending(self, *, limit: int = 100) -> list[OutboxEventRecord]:
        with managed_session(self._session_factory) as db:
            rows = db.execute(
                select(CourseOutboxEventModel)
                .where(CourseOutboxEventModel.status == OutboxEventStatus.PENDING.value)
                .order_by(CourseOutboxEventModel.created_at.asc())
                .limit(limit)
            ).scalars()
            return [self._to_entity(row) for row in rows]

    @staticmethod
    def _to_model(event: OutboxEventRecord) -> CourseOutboxEventModel:
        return CourseOutboxEventModel(
            event_id=event.event_id,
            aggregate_type=event.aggregate_type,
            aggregate_id=event.aggregate_id,
            event_type=event.event_type.value,
            payload_json=event.payload_json,
            status=event.status.value,
            attempt_count=event.attempt_count,
            available_at=event.available_at,
            created_at=event.created_at,
            processed_at=event.processed_at,
            last_error=event.last_error,
        )

    @staticmethod
    def _fill_model(model: CourseOutboxEventModel, event: OutboxEventRecord) -> None:
        model.aggregate_type = event.aggregate_type
        model.aggregate_id = event.aggregate_id
        model.event_type = event.event_type.value
        model.payload_json = event.payload_json
        model.status = event.status.value
        model.attempt_count = event.attempt_count
        model.available_at = event.available_at
        model.created_at = event.created_at
        model.processed_at = event.processed_at
        model.last_error = event.last_error

    @staticmethod
    def _to_entity(model: CourseOutboxEventModel) -> OutboxEventRecord:
        return OutboxEventRecord(
            event_id=model.event_id,
            aggregate_type=model.aggregate_type,
            aggregate_id=model.aggregate_id,
            event_type=OutboxEventType(model.event_type),
            payload_json=model.payload_json,
            status=OutboxEventStatus(model.status),
            attempt_count=int(model.attempt_count),
            available_at=model.available_at,
            created_at=model.created_at,
            processed_at=model.processed_at,
            last_error=model.last_error,
        )
