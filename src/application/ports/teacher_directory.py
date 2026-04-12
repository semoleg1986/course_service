"""Порт каталога преподавателей (users_service)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True, slots=True)
class TeacherInfo:
    """Снэпшот профиля преподавателя из users_service."""

    teacher_id: str
    display_name: str
    status: str
    roles: list[str]


class TeacherDirectory(Protocol):
    """Контракт получения профиля преподавателя."""

    def get_teacher(self, teacher_id: str) -> TeacherInfo | None:
        """Возвращает профиль преподавателя по id либо None."""
