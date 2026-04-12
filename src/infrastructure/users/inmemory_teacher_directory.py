"""In-memory каталог преподавателей."""

from __future__ import annotations

from src.application.ports.teacher_directory import TeacherInfo


class InMemoryTeacherDirectory:
    """In-memory реализация TeacherDirectory для локальной разработки и unit-тестов."""

    def __init__(self, teachers: dict[str, TeacherInfo] | None = None) -> None:
        self._teachers = teachers or {
            "teacher-1": TeacherInfo(
                teacher_id="teacher-1",
                display_name="Teacher 1",
                status="active",
                roles=["teacher"],
            ),
            "teacher-22": TeacherInfo(
                teacher_id="teacher-22",
                display_name="Teacher 22",
                status="active",
                roles=["teacher"],
            ),
            "teacher-99": TeacherInfo(
                teacher_id="teacher-99",
                display_name="Teacher 99",
                status="active",
                roles=["teacher"],
            ),
        }

    def get_teacher(self, teacher_id: str) -> TeacherInfo | None:
        """Возвращает преподавателя по id."""

        normalized = teacher_id.strip()
        if not normalized:
            return None
        return self._teachers.get(normalized)
