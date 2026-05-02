"""In-memory read model для проверки доступа."""

from __future__ import annotations

from datetime import datetime


class InMemoryAccessReadModel:
    """Простая in-memory реализация AccessReadModel."""

    def __init__(self) -> None:
        self._course_owner: dict[str, str] = {}
        self._access_grant_status: dict[tuple[str, str], str] = {}
        self._enrollment_status: dict[tuple[str, str], str] = {}
        self._lesson_progress: dict[tuple[str, str, str], dict[str, object | None]] = {}
        self._course_progress_summary: dict[
            tuple[str, str], tuple[str, float, int, int, datetime | None]
        ] = {}
        self._processed_access_events: set[str] = set()

    def get_course_owner(self, course_id: str) -> str | None:
        return self._course_owner.get(course_id)

    def get_access_grant_status(self, course_id: str, student_id: str) -> str | None:
        return self._access_grant_status.get((course_id, student_id))

    def get_enrollment_status(self, course_id: str, student_id: str) -> str | None:
        return self._enrollment_status.get((course_id, student_id))

    def list_access_grants_by_student(self, student_id: str) -> list[tuple[str, str]]:
        return sorted(
            [
                (course_id, status)
                for (course_id, sid), status in self._access_grant_status.items()
                if sid == student_id
            ],
            key=lambda item: item[0],
        )

    def list_enrollments_by_student(self, student_id: str) -> list[tuple[str, str]]:
        return sorted(
            [
                (course_id, status)
                for (course_id, sid), status in self._enrollment_status.items()
                if sid == student_id
            ],
            key=lambda item: item[0],
        )

    def seed_course_owner(self, course_id: str, owner_account_id: str) -> None:
        """Заполняет read model владельцем курса."""

        self._course_owner[course_id] = owner_account_id

    def seed_access_grant_status(
        self, course_id: str, student_id: str, status: str
    ) -> None:
        """Заполняет read model статусом доступа."""

        self._access_grant_status[(course_id, student_id)] = status

    def seed_enrollment_status(
        self, course_id: str, student_id: str, status: str
    ) -> None:
        """Заполняет read model статусом enrollment."""

        self._enrollment_status[(course_id, student_id)] = status

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
        """Создает или обновляет in-memory projection прогресса по уроку."""
        self._lesson_progress[(course_id, student_id, lesson_id)] = {
            "progress_id": progress_id,
            "module_id": module_id,
            "status": status,
            "created_at": created_at,
            "created_by": created_by,
            "updated_at": updated_at,
            "updated_by": updated_by,
            "version": version,
            "started_at": started_at,
            "completed_at": completed_at,
            "last_activity_at": last_activity_at,
        }

    def get_lesson_progress(
        self, *, course_id: str, student_id: str, lesson_id: str
    ) -> dict[str, object] | None:
        payload = self._lesson_progress.get((course_id, student_id, lesson_id))
        return dict(payload) if payload is not None else None

    def list_completed_lesson_ids(
        self, *, course_id: str, student_id: str
    ) -> list[str]:
        """Возвращает lesson_id завершенных уроков курса."""
        items = [
            lesson_id
            for (cid, sid, lesson_id), payload in self._lesson_progress.items()
            if cid == course_id
            and sid == student_id
            and payload.get("status") == "completed"
        ]
        return sorted(items)

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
        self._course_progress_summary[(course_id, student_id)] = (
            status,
            progress_percent,
            completed_lessons,
            total_lessons,
            completed_at,
        )

    def get_course_progress_summary(
        self, *, course_id: str, student_id: str
    ) -> tuple[str, float, int, int, datetime | None] | None:
        """Возвращает summary прогресса по курсу."""
        return self._course_progress_summary.get((course_id, student_id))

    def apply_access_granted_event(
        self,
        *,
        event_id: str,
        course_id: str,
        student_id: str,
        granted_status: str,
    ) -> bool:
        """Применяет access_granted event с replay-safe dedup."""

        if event_id in self._processed_access_events:
            return False
        self._processed_access_events.add(event_id)
        self._access_grant_status[(course_id, student_id)] = granted_status
        return True
