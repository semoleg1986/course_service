from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from src.domain.errors import InvariantViolationError
from src.domain.shared.entity import EntityMeta
from src.domain.shared.statuses import PublishState
from .value_objects import CourseSchedule, CourseSlug, SeoMetadata


@dataclass(slots=True)
class Lesson:
    """
    Сущность урока внутри модуля.

    :param lesson_id: Идентификатор урока.
    :type lesson_id: str
    :param title: Название урока.
    :type title: str
    :param meta: Технические метаданные сущности.
    :type meta: EntityMeta
    """

    lesson_id: str
    title: str
    meta: EntityMeta

    @classmethod
    def create(
        cls,
        lesson_id: str,
        title: str,
        created_at: datetime,
        created_by: str,
    ) -> "Lesson":
        """Создать новый урок."""
        return cls(
            lesson_id=lesson_id,
            title=title,
            meta=EntityMeta.create(at=created_at, actor_id=created_by),
        )


@dataclass(slots=True)
class Module:
    """
    Сущность модуля внутри курса.

    :param module_id: Идентификатор модуля.
    :type module_id: str
    :param title: Название модуля.
    :type title: str
    :param meta: Технические метаданные.
    :type meta: EntityMeta
    :param lessons: Список уроков модуля.
    :type lessons: list[Lesson]
    """

    module_id: str
    title: str
    meta: EntityMeta
    lessons: list[Lesson] = field(default_factory=list)

    @classmethod
    def create(
        cls,
        module_id: str,
        title: str,
        created_at: datetime,
        created_by: str,
    ) -> "Module":
        """Создать новый модуль."""
        return cls(
            module_id=module_id,
            title=title,
            meta=EntityMeta.create(at=created_at, actor_id=created_by),
        )

    def add_lesson(self, lesson: Lesson, changed_at: datetime, changed_by: str) -> None:
        """Добавить урок в модуль."""
        self.lessons.append(lesson)
        self.meta.touch(at=changed_at, actor_id=changed_by)


@dataclass(slots=True)
class Course:
    """
    Aggregate Root курса.

    :param course_id: Идентификатор курса.
    :type course_id: str
    :param title: Название курса.
    :type title: str
    :param teacher_id: Идентификатор преподавателя (account/user id из users_service).
    :type teacher_id: str
    :param slug: SEO slug курса.
    :type slug: CourseSlug
    :param schedule: Расписание курса.
    :type schedule: CourseSchedule
    :param seo: SEO-метаданные.
    :type seo: SeoMetadata
    :param meta: Технические метаданные агрегата.
    :type meta: EntityMeta
    :param publish_state: Состояние публикации.
    :type publish_state: PublishState
    :param modules: Дочерние модули.
    :type modules: list[Module]
    """

    course_id: str
    title: str
    teacher_id: str
    slug: CourseSlug
    schedule: CourseSchedule
    seo: SeoMetadata
    meta: EntityMeta
    publish_state: PublishState = PublishState.DRAFT
    modules: list[Module] = field(default_factory=list)

    @classmethod
    def create(
        cls,
        course_id: str,
        title: str,
        teacher_id: str,
        slug: CourseSlug,
        schedule: CourseSchedule,
        seo: SeoMetadata,
        created_at: datetime,
        created_by: str,
    ) -> "Course":
        """Создать новый курс."""
        if not teacher_id.strip():
            raise InvariantViolationError("teacher_id обязателен")
        return cls(
            course_id=course_id,
            title=title,
            teacher_id=teacher_id,
            slug=slug,
            schedule=schedule,
            seo=seo,
            meta=EntityMeta.create(at=created_at, actor_id=created_by),
        )

    @property
    def lessons_total(self) -> int:
        """Общее число уроков в курсе."""
        return sum(len(module.lessons) for module in self.modules)

    @property
    def estimated_duration_hours(self) -> int:
        """
        Расчетная длительность курса в часах.

        Бизнес-правило: 1 урок = 1 час.
        """
        return self.lessons_total

    def add_module(self, module: Module, changed_at: datetime, changed_by: str) -> None:
        """Добавить модуль в курс."""
        self.modules.append(module)
        self.meta.touch(at=changed_at, actor_id=changed_by)

    def publish(self, changed_at: datetime, changed_by: str) -> None:
        """
        Опубликовать курс.

        :raises InvariantViolationError: Если нарушены инварианты структуры/SEO.
        """
        if not self.modules:
            raise InvariantViolationError("Курс должен содержать хотя бы один модуль")
        if any(not module.lessons for module in self.modules):
            raise InvariantViolationError("В каждом модуле должен быть хотя бы один урок")
        if not self.slug.value or not self.seo.meta_title or not self.seo.meta_description:
            raise InvariantViolationError("Для публикации обязателен SEO-минимум")
        self.publish_state = PublishState.PUBLISHED
        self.meta.touch(at=changed_at, actor_id=changed_by)

    def archive(self, changed_at: datetime, changed_by: str) -> None:
        """Архивировать курс (soft state transition)."""
        self.publish_state = PublishState.ARCHIVED
        self.meta.mark_archived(at=changed_at, actor_id=changed_by)
