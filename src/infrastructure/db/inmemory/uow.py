"""In-memory UnitOfWork для write-side use-case курса."""

from __future__ import annotations

import copy
from dataclasses import dataclass

from src.application.ports.repositories import RepositoryProvider
from src.infrastructure.db.inmemory.access_read_model import InMemoryAccessReadModel
from src.infrastructure.db.inmemory.audit_evidence_repository import (
    InMemoryAuditEvidenceRepository,
)
from src.infrastructure.db.inmemory.course_repository import InMemoryCourseRepository
from src.infrastructure.db.inmemory.outbox_repository import InMemoryOutboxRepository


@dataclass(slots=True)
class InMemoryRepositoryProvider(RepositoryProvider):
    """Набор in-memory write-side репозиториев."""

    courses: InMemoryCourseRepository
    access_read_model: InMemoryAccessReadModel
    audit_evidence: InMemoryAuditEvidenceRepository
    outbox: InMemoryOutboxRepository


class InMemoryUnitOfWork:
    """Простая транзакционная оболочка для in-memory write-side."""

    def __init__(
        self,
        *,
        course_repository: InMemoryCourseRepository,
        access_read_model: InMemoryAccessReadModel,
        audit_evidence: InMemoryAuditEvidenceRepository,
        outbox: InMemoryOutboxRepository,
    ) -> None:
        self._course_repository = course_repository
        self._access_read_model = access_read_model
        self._audit_evidence = audit_evidence
        self._outbox = outbox
        self._snapshot = (
            copy.deepcopy(course_repository._by_id),
            copy.deepcopy(access_read_model._course_owner),
            copy.deepcopy(access_read_model._access_grant_status),
            copy.deepcopy(access_read_model._enrollment_status),
            copy.deepcopy(access_read_model._lesson_progress),
            copy.deepcopy(access_read_model._course_progress_summary),
            copy.deepcopy(access_read_model._processed_access_events),
            copy.deepcopy(audit_evidence._items),
            copy.deepcopy(outbox._items),
        )
        self._repositories = InMemoryRepositoryProvider(
            courses=course_repository,
            access_read_model=access_read_model,
            audit_evidence=audit_evidence,
            outbox=outbox,
        )

    @property
    def repositories(self) -> InMemoryRepositoryProvider:
        return self._repositories

    def commit(self) -> None:
        return

    def rollback(self) -> None:
        (
            self._course_repository._by_id,
            self._access_read_model._course_owner,
            self._access_read_model._access_grant_status,
            self._access_read_model._enrollment_status,
            self._access_read_model._lesson_progress,
            self._access_read_model._course_progress_summary,
            self._access_read_model._processed_access_events,
            self._audit_evidence._items,
            self._outbox._items,
        ) = copy.deepcopy(self._snapshot)

    def close(self) -> None:
        return
