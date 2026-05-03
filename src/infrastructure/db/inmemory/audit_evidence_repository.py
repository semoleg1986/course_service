"""In-memory retained audit evidence repository."""

from __future__ import annotations

from src.application.ports.audit_evidence import AuditEvidenceRecord


class InMemoryAuditEvidenceRepository:
    """Append-only retained audit evidence в памяти процесса."""

    def __init__(self) -> None:
        self._items: list[AuditEvidenceRecord] = []

    def append(self, record: AuditEvidenceRecord) -> None:
        self._items.append(record)

    def list_all(self) -> list[AuditEvidenceRecord]:
        return list(self._items)
