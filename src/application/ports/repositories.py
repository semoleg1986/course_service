"""Провайдер write-side репозиториев для UnitOfWork."""

from __future__ import annotations

from typing import Protocol

from src.application.ports.access_read_model import AccessReadModel
from src.application.ports.audit_evidence import AuditEvidenceRepository
from src.domain.content.course.repository import CourseRepository


class RepositoryProvider(Protocol):
    """Набор write-side репозиториев текущей транзакции."""

    @property
    def courses(self) -> CourseRepository:
        """Репозиторий агрегата Course."""

    @property
    def access_read_model(self) -> AccessReadModel:
        """Projection/read-model для write-side синхронизации."""

    @property
    def audit_evidence(self) -> AuditEvidenceRepository:
        """Append-only retained audit evidence."""
