"""SQLAlchemy retained audit evidence repository."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from src.application.ports.audit_evidence import AuditEvidenceRecord
from src.infrastructure.db.sqlalchemy.models import AuditEvidenceModel
from src.infrastructure.db.sqlalchemy.session import (
    managed_session,
    managed_transaction,
)


class SqlalchemyAuditEvidenceRepository:
    """Append-only retained audit evidence на SQLAlchemy."""

    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    def append(self, record: AuditEvidenceRecord) -> None:
        with managed_transaction(self._session_factory) as db:
            db.add(
                AuditEvidenceModel(
                    audit_id=record.audit_id,
                    action=record.action,
                    occurred_at=record.occurred_at,
                    result=record.result,
                    actor_id=record.actor_id,
                    actor_roles=list(record.actor_roles),
                    target_type=record.target_type,
                    target_id=record.target_id,
                    reason=record.reason,
                    reason_code=record.reason_code,
                    request_id=record.request_id,
                    correlation_id=record.correlation_id,
                    course_id=record.course_id,
                )
            )

    def list_all(self) -> list[AuditEvidenceRecord]:
        with managed_session(self._session_factory) as db:
            models = (
                db.execute(
                    select(AuditEvidenceModel).order_by(
                        AuditEvidenceModel.occurred_at.asc()
                    )
                )
                .scalars()
                .all()
            )
            return [
                AuditEvidenceRecord(
                    audit_id=model.audit_id,
                    action=model.action,
                    occurred_at=model.occurred_at,
                    result=model.result,
                    actor_id=model.actor_id,
                    actor_roles=tuple(model.actor_roles or []),
                    target_type=model.target_type,
                    target_id=model.target_id,
                    reason=model.reason,
                    reason_code=model.reason_code,
                    request_id=model.request_id,
                    correlation_id=model.correlation_id,
                    course_id=model.course_id,
                )
                for model in models
            ]
