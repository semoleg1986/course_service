from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from src.domain.errors import InvariantViolationError
from src.domain.shared.entity import EntityMeta
from src.domain.shared.statuses import LessonProgressStatus


@dataclass(slots=True)
class LessonProgress:
    """
    Прогресс ученика по конкретному уроку.

    Хранит минимальный доменный baseline для Sprint 3:
    статус урока и основные временные метки жизненного цикла.
    """

    progress_id: str
    course_id: str
    module_id: str
    lesson_id: str
    student_id: str
    status: LessonProgressStatus
    meta: EntityMeta
    started_at: datetime | None = None
    completed_at: datetime | None = None
    last_activity_at: datetime | None = None

    @classmethod
    def create(
        cls,
        *,
        progress_id: str,
        course_id: str,
        module_id: str,
        lesson_id: str,
        student_id: str,
        created_at: datetime,
        created_by: str,
    ) -> "LessonProgress":
        """Создает новый трекер прогресса в состоянии not_started."""
        cls._ensure_id(progress_id, "progress_id")
        cls._ensure_id(course_id, "course_id")
        cls._ensure_id(module_id, "module_id")
        cls._ensure_id(lesson_id, "lesson_id")
        cls._ensure_id(student_id, "student_id")
        return cls(
            progress_id=progress_id,
            course_id=course_id,
            module_id=module_id,
            lesson_id=lesson_id,
            student_id=student_id,
            status=LessonProgressStatus.NOT_STARTED,
            meta=EntityMeta.create(at=created_at, actor_id=created_by),
        )

    @classmethod
    def restore(
        cls,
        *,
        progress_id: str,
        course_id: str,
        module_id: str,
        lesson_id: str,
        student_id: str,
        status: LessonProgressStatus,
        created_at: datetime,
        created_by: str,
        updated_at: datetime,
        updated_by: str,
        version: int,
        started_at: datetime | None,
        completed_at: datetime | None,
        last_activity_at: datetime | None,
    ) -> "LessonProgress":
        """Восстанавливает прогресс урока из persistence/read-model."""
        return cls(
            progress_id=progress_id,
            course_id=course_id,
            module_id=module_id,
            lesson_id=lesson_id,
            student_id=student_id,
            status=status,
            meta=EntityMeta(
                version=version,
                created_at=created_at,
                created_by=created_by,
                updated_at=updated_at,
                updated_by=updated_by,
            ),
            started_at=started_at,
            completed_at=completed_at,
            last_activity_at=last_activity_at,
        )

    def start(self, *, changed_at: datetime, changed_by: str) -> None:
        """
        Переводит урок в in_progress.

        Повторный start для completed-урока запрещен,
        а для уже начатого урока работает как idempotent touch.
        """
        if self.status == LessonProgressStatus.COMPLETED:
            raise InvariantViolationError("Нельзя заново начать уже завершенный урок.")
        if self.started_at is None:
            self.started_at = changed_at
        self.last_activity_at = changed_at
        self.status = LessonProgressStatus.IN_PROGRESS
        self.meta.touch(at=changed_at, actor_id=changed_by)

    def complete(self, *, changed_at: datetime, changed_by: str) -> None:
        """
        Завершает урок.

        Повторный complete работает идемпотентно и не меняет состояние.
        """
        if self.status == LessonProgressStatus.COMPLETED:
            return
        if self.started_at is None:
            self.started_at = changed_at
        self.completed_at = changed_at
        self.last_activity_at = changed_at
        self.status = LessonProgressStatus.COMPLETED
        self.meta.touch(at=changed_at, actor_id=changed_by)

    def mark_activity(self, *, changed_at: datetime, changed_by: str) -> None:
        """Фиксирует активность внутри урока без завершения."""
        if self.status == LessonProgressStatus.NOT_STARTED:
            self.start(changed_at=changed_at, changed_by=changed_by)
            return
        if self.status == LessonProgressStatus.COMPLETED:
            raise InvariantViolationError(
                "Нельзя обновлять активность завершенного урока."
            )
        self.last_activity_at = changed_at
        self.meta.touch(at=changed_at, actor_id=changed_by)

    @staticmethod
    def _ensure_id(value: str, field_name: str) -> None:
        if not value.strip():
            raise InvariantViolationError(f"{field_name} обязателен")
