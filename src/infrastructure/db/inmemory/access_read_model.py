"""In-memory read model для проверки доступа."""

from __future__ import annotations


class InMemoryAccessReadModel:
    """Простая in-memory реализация AccessReadModel."""

    def __init__(self) -> None:
        self._course_owner: dict[str, str] = {}
        self._access_grant_status: dict[tuple[str, str], str] = {}
        self._enrollment_status: dict[tuple[str, str], str] = {}

    def get_course_owner(self, course_id: str) -> str | None:
        return self._course_owner.get(course_id)

    def get_access_grant_status(self, course_id: str, student_id: str) -> str | None:
        return self._access_grant_status.get((course_id, student_id))

    def get_enrollment_status(self, course_id: str, student_id: str) -> str | None:
        return self._enrollment_status.get((course_id, student_id))

    def seed_course_owner(self, course_id: str, owner_account_id: str) -> None:
        """Заполняет read model владельцем курса."""

        self._course_owner[course_id] = owner_account_id

    def seed_access_grant_status(self, course_id: str, student_id: str, status: str) -> None:
        """Заполняет read model статусом доступа."""

        self._access_grant_status[(course_id, student_id)] = status

    def seed_enrollment_status(self, course_id: str, student_id: str, status: str) -> None:
        """Заполняет read model статусом enrollment."""

        self._enrollment_status[(course_id, student_id)] = status

