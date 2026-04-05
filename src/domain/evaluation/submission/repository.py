from __future__ import annotations

from typing import Protocol

from .entity import Submission


class SubmissionRepository(Protocol):
    """Репозиторий агрегата Submission."""

    def get(self, submission_id: str) -> Submission | None:
        """Получить submission по id."""

    def save(self, submission: Submission) -> None:
        """Сохранить агрегат Submission."""
