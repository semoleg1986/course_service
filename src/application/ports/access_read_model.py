"""Read-model порт для проверки доступа к курсу."""

from __future__ import annotations

from typing import Protocol


class AccessReadModel(Protocol):
    """Контракт чтения данных для use-case проверки доступа."""

    def get_course_owner(self, course_id: str) -> str | None:
        """Возвращает account_id владельца курса или None."""

    def get_access_grant_status(self, course_id: str, student_id: str) -> str | None:
        """Возвращает статус grant для пары курс/ученик."""

    def get_enrollment_status(self, course_id: str, student_id: str) -> str | None:
        """Возвращает статус enrollment для пары курс/ученик."""

    def list_access_grants_by_student(self, student_id: str) -> list[tuple[str, str]]:
        """Возвращает пары (course_id, status) по access grants ученика."""

    def list_enrollments_by_student(self, student_id: str) -> list[tuple[str, str]]:
        """Возвращает пары (course_id, status) по enrollments ученика."""

    def apply_access_granted_event(
        self,
        *,
        event_id: str,
        course_id: str,
        student_id: str,
        granted_status: str,
    ) -> bool:
        """Применяет access_granted event к projection. False, если replay/dedup."""
