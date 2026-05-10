"""SQLAlchemy UnitOfWork для write-side use-case курса."""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.orm import Session, sessionmaker

from src.application.ports.repositories import RepositoryProvider
from src.infrastructure.db.sqlalchemy.access_read_model_sqlalchemy import (
    SqlalchemyAccessReadModel,
)
from src.infrastructure.db.sqlalchemy.audit_evidence_repository_sqlalchemy import (
    SqlalchemyAuditEvidenceRepository,
)
from src.infrastructure.db.sqlalchemy.course_repository_sqlalchemy import (
    SqlalchemyCourseRepository,
)
from src.infrastructure.db.sqlalchemy.outbox_repository_sqlalchemy import (
    SqlalchemyOutboxRepository,
)
from src.infrastructure.db.sqlalchemy.session import (
    reset_current_session,
    set_current_session,
)


@dataclass(slots=True)
class SqlalchemyRepositoryProvider(RepositoryProvider):
    """Набор SQLAlchemy write-side репозиториев."""

    courses: SqlalchemyCourseRepository
    access_read_model: SqlalchemyAccessReadModel
    audit_evidence: SqlalchemyAuditEvidenceRepository
    outbox: SqlalchemyOutboxRepository


class SqlalchemyUnitOfWork:
    """Единая SQL session на один write use-case."""

    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory
        self._session = session_factory()
        self._token = set_current_session(self._session)
        self._repositories = SqlalchemyRepositoryProvider(
            courses=SqlalchemyCourseRepository(session_factory),
            access_read_model=SqlalchemyAccessReadModel(session_factory),
            audit_evidence=SqlalchemyAuditEvidenceRepository(session_factory),
            outbox=SqlalchemyOutboxRepository(session_factory),
        )

    @property
    def repositories(self) -> SqlalchemyRepositoryProvider:
        return self._repositories

    def commit(self) -> None:
        self._session.commit()

    def rollback(self) -> None:
        self._session.rollback()

    def close(self) -> None:
        reset_current_session(self._token)
        self._session.close()
