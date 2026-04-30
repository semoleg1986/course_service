from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from src.domain.errors import InvariantViolationError
from src.domain.shared.entity import EntityMeta
from src.domain.shared.statuses import PublishState

from .value_objects import (
    CourseAudience,
    CourseDeliverySettings,
    CoursePricing,
    CourseSchedule,
    CourseSlug,
    SeoMetadata,
)


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
    description: str | None
    content_type: str
    content_ref: str | None
    duration_minutes: int | None
    is_preview: bool
    released_at: datetime | None
    status: PublishState
    meta: EntityMeta

    @classmethod
    def create(
        cls,
        lesson_id: str,
        title: str,
        created_at: datetime,
        created_by: str,
        description: str | None = None,
        content_type: str = "video",
        content_ref: str | None = None,
        duration_minutes: int | None = None,
        is_preview: bool = False,
        released_at: datetime | None = None,
    ) -> "Lesson":
        """Создать новый урок."""
        if duration_minutes is not None and duration_minutes < 1:
            raise InvariantViolationError("duration_minutes должен быть >= 1.")
        return cls(
            lesson_id=lesson_id,
            title=title,
            description=description,
            content_type=content_type,
            content_ref=content_ref,
            duration_minutes=duration_minutes,
            is_preview=is_preview,
            released_at=released_at,
            status=PublishState.DRAFT,
            meta=EntityMeta.create(at=created_at, actor_id=created_by),
        )

    def update(
        self,
        *,
        title: str | None,
        description: str | None,
        content_type: str | None,
        content_ref: str | None,
        duration_minutes: int | None,
        is_preview: bool | None,
        released_at: datetime | None,
        status: str | None,
        changed_at: datetime,
        changed_by: str,
    ) -> None:
        if title is not None:
            self.title = title
        if description is not None:
            self.description = description
        if content_type is not None:
            self.content_type = content_type
        if content_ref is not None:
            self.content_ref = content_ref
        if duration_minutes is not None:
            if duration_minutes < 1:
                raise InvariantViolationError("duration_minutes должен быть >= 1.")
            self.duration_minutes = duration_minutes
        if is_preview is not None:
            self.is_preview = is_preview
        if released_at is not None:
            self.released_at = released_at
        if status is not None:
            self.status = PublishState(status)
        self.meta.touch(at=changed_at, actor_id=changed_by)


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
    description: str | None
    is_required: bool
    released_at: datetime | None
    status: PublishState
    meta: EntityMeta
    lessons: list[Lesson] = field(default_factory=list)

    @classmethod
    def create(
        cls,
        module_id: str,
        title: str,
        created_at: datetime,
        created_by: str,
        description: str | None = None,
        is_required: bool = True,
        released_at: datetime | None = None,
    ) -> "Module":
        """Создать новый модуль."""
        return cls(
            module_id=module_id,
            title=title,
            description=description,
            is_required=is_required,
            released_at=released_at,
            status=PublishState.DRAFT,
            meta=EntityMeta.create(at=created_at, actor_id=created_by),
        )

    def add_lesson(self, lesson: Lesson, changed_at: datetime, changed_by: str) -> None:
        """Добавить урок в модуль."""
        self.lessons.append(lesson)
        self.meta.touch(at=changed_at, actor_id=changed_by)

    def update(
        self,
        *,
        title: str | None,
        description: str | None,
        is_required: bool | None,
        released_at: datetime | None,
        status: str | None,
        changed_at: datetime,
        changed_by: str,
    ) -> None:
        if title is not None:
            self.title = title
        if description is not None:
            self.description = description
        if is_required is not None:
            self.is_required = is_required
        if released_at is not None:
            self.released_at = released_at
        if status is not None:
            self.status = PublishState(status)
        self.meta.touch(at=changed_at, actor_id=changed_by)


@dataclass(slots=True)
class Course:
    """
    Aggregate Root курса.

    :param course_id: Идентификатор курса.
    :type course_id: str
    :param title: Название курса.
    :type title: str
    :param description: Краткое описание курса.
    :type description: str | None
    :param teacher_id: Идентификатор преподавателя (account/user id из users_service).
    :type teacher_id: str
    :param teacher_display_name: Снэпшот отображаемого имени преподавателя для каталога.
    :type teacher_display_name: str | None
    :param slug: SEO slug курса.
    :type slug: CourseSlug
    :param schedule: Расписание курса.
    :type schedule: CourseSchedule
    :param pricing: Ценовые параметры.
    :type pricing: CoursePricing
    :param audience: Параметры аудитории.
    :type audience: CourseAudience
    :param delivery: Настройки доставки/представления.
    :type delivery: CourseDeliverySettings
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
    description: str | None
    teacher_id: str
    teacher_display_name: str | None
    slug: CourseSlug
    schedule: CourseSchedule
    pricing: CoursePricing
    audience: CourseAudience
    delivery: CourseDeliverySettings
    seo: SeoMetadata
    meta: EntityMeta
    publish_state: PublishState = PublishState.DRAFT
    published_at: datetime | None = None
    published_by_admin_id: str | None = None
    modules: list[Module] = field(default_factory=list)

    @classmethod
    def create(
        cls,
        course_id: str,
        title: str,
        description: str | None,
        teacher_id: str,
        slug: CourseSlug,
        schedule: CourseSchedule,
        seo: SeoMetadata,
        created_at: datetime,
        created_by: str,
        teacher_display_name: str | None = None,
        pricing: CoursePricing | None = None,
        audience: CourseAudience | None = None,
        delivery: CourseDeliverySettings | None = None,
    ) -> "Course":
        """Создать новый курс."""
        if not teacher_id.strip():
            raise InvariantViolationError("teacher_id обязателен")
        return cls(
            course_id=course_id,
            title=title,
            description=description.strip() if description else None,
            teacher_id=teacher_id,
            teacher_display_name=(
                teacher_display_name.strip() if teacher_display_name else None
            ),
            slug=slug,
            schedule=schedule,
            pricing=pricing or CoursePricing(),
            audience=audience or CourseAudience(),
            delivery=delivery or CourseDeliverySettings(),
            seo=seo,
            meta=EntityMeta.create(at=created_at, actor_id=created_by),
        )

    @property
    def modules_count(self) -> int:
        """Количество модулей курса."""
        return len(self.modules)

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

    @property
    def is_free(self) -> bool:
        """Флаг бесплатного курса."""
        return self.pricing.price == 0

    @property
    def archived_at(self) -> datetime | None:
        """Дата архивирования."""
        return self.meta.archived_at

    @property
    def archived_by(self) -> str | None:
        """Кто архивировал курс."""
        return self.meta.archived_by

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
        published_modules = [
            module for module in self.modules if module.status == PublishState.PUBLISHED
        ]
        if not published_modules:
            raise InvariantViolationError(
                "Для публикации нужен хотя бы один published модуль."
            )
        for module in published_modules:
            if not any(
                lesson.status == PublishState.PUBLISHED for lesson in module.lessons
            ):
                raise InvariantViolationError(
                    "В каждом published модуле должен быть хотя бы один published урок."
                )
        if (
            not self.slug.value
            or not self.seo.meta_title
            or not self.seo.meta_description
        ):
            raise InvariantViolationError("Для публикации обязателен SEO-минимум")
        self.publish_state = PublishState.PUBLISHED
        self.published_at = changed_at
        self.published_by_admin_id = changed_by
        self.meta.touch(at=changed_at, actor_id=changed_by)

    def archive(self, changed_at: datetime, changed_by: str) -> None:
        """Архивировать курс (soft state transition)."""
        self.publish_state = PublishState.ARCHIVED
        self.meta.mark_archived(at=changed_at, actor_id=changed_by)
