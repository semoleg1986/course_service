"""In-memory checker связи parent-student."""

from __future__ import annotations


class InMemoryParentStudentRelationChecker:
    """In-memory реализация ParentStudentRelationChecker."""

    def __init__(self, relations: set[tuple[str, str]] | None = None) -> None:
        self._relations = relations or {("parent-1", "student-1")}

    def has_relation(self, parent_id: str, student_id: str) -> bool:
        return (parent_id.strip(), student_id.strip()) in self._relations
