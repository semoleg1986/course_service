"""Read-model порт для проверки доступа к курсу."""

from __future__ import annotations

from datetime import datetime
from typing import Protocol


class AccessReadModel(Protocol):
    """Контракт чтения данных для use-case проверки доступа."""

    def get_course_owner(self, course_id: str) -> str | None:
        """Возвращает account_id владельца курса или None."""

    def seed_course_owner(self, course_id: str, owner_account_id: str) -> None:
        """Создает или обновляет projection владельца курса."""

    def get_access_grant_status(self, course_id: str, student_id: str) -> str | None:
        """Возвращает статус grant для пары курс/ученик."""

    def get_enrollment_status(self, course_id: str, student_id: str) -> str | None:
        """Возвращает статус enrollment для пары курс/ученик."""

    def list_access_grants_by_student(self, student_id: str) -> list[tuple[str, str]]:
        """Возвращает пары (course_id, status) по access grants ученика."""

    def list_enrollments_by_student(self, student_id: str) -> list[tuple[str, str]]:
        """Возвращает пары (course_id, status) по enrollments ученика."""

    def upsert_lesson_progress(
        self,
        *,
        course_id: str,
        module_id: str,
        lesson_id: str,
        student_id: str,
        progress_id: str,
        status: str,
        created_at: datetime,
        created_by: str,
        updated_at: datetime,
        updated_by: str,
        version: int,
        started_at: datetime | None,
        completed_at: datetime | None,
        last_activity_at: datetime | None,
    ) -> None:
        """Создает или обновляет projection прогресса по уроку."""

    def get_lesson_progress(
        self, *, course_id: str, student_id: str, lesson_id: str
    ) -> dict[str, object] | None:
        """Возвращает projection прогресса по уроку или None."""

    def list_completed_lesson_ids(
        self, *, course_id: str, student_id: str
    ) -> list[str]:
        """Возвращает список завершенных уроков ученика внутри курса."""

    def store_course_progress_summary(
        self,
        *,
        course_id: str,
        student_id: str,
        status: str,
        progress_percent: float,
        completed_lessons: int,
        total_lessons: int,
        completed_at: datetime | None,
    ) -> None:
        """Сохраняет агрегированный summary прогресса по курсу."""

    def get_course_progress_summary(
        self, *, course_id: str, student_id: str
    ) -> tuple[str, float, int, int, datetime | None] | None:
        """Возвращает summary прогресса по курсу или None."""

    def apply_access_granted_event(
        self,
        *,
        event_id: str,
        course_id: str,
        student_id: str,
        granted_status: str,
    ) -> bool:
        """Применяет access_granted event к projection. False, если replay/dedup."""
