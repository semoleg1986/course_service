"""Порт проверки связи parent-student в users_service."""

from __future__ import annotations

from typing import Protocol


class ParentStudentRelationChecker(Protocol):
    """Контракт проверки активной связи parent-student."""

    def has_relation(self, parent_id: str, student_id: str) -> bool:
        """Возвращает True, если parent связан со student активной связью."""
