"""Port for looking up parents by student id in users_service."""

from __future__ import annotations

from typing import Protocol


class StudentParentDirectory(Protocol):
    """Contract for retrieving active parent ids for a student."""

    def list_parent_ids(self, student_id: str) -> list[str]:
        """Return active parent ids for the given student."""
