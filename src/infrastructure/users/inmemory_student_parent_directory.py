"""In-memory lookup of parents by student id."""

from __future__ import annotations


class InMemoryStudentParentDirectory:
    """In-memory implementation for tests and local runs."""

    def __init__(self, mappings: dict[str, list[str]] | None = None) -> None:
        self._mappings = mappings or {"student-1": ["parent-1"]}

    def list_parent_ids(self, student_id: str) -> list[str]:
        return list(self._mappings.get(student_id.strip(), []))
