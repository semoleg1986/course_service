"""Handlers управления курсом."""

from __future__ import annotations

import re
from uuid import uuid4

from src.application.common.dto import CourseResult
from src.application.common.mappers import to_course_result
from src.application.courses.commands.dto import (
    AddLessonCommand,
    AddModuleCommand,
    ArchiveCourseCommand,
    CreateCourseCommand,
    PublishCourseCommand,
    UpdateCourseCommand,
    UpdateLessonCommand,
    UpdateModuleCommand,
)
from src.application.courses.queries.dto import GetCourseByIdQuery
from src.application.ports.clock import Clock
from src.application.ports.teacher_directory import TeacherDirectory
from src.domain.content.course.entity import Course, Lesson, Module
from src.domain.content.course.repository import CourseRepository
from src.domain.content.course.value_objects import (
    CourseAudience,
    CourseDeliverySettings,
    CoursePricing,
    CourseSchedule,
    CourseSlug,
    SeoMetadata,
)
from src.domain.errors import AccessDeniedError, InvariantViolationError, NotFoundError

_SLUG_CLEANUP = re.compile(r"[^a-z0-9]+")


def _slugify(value: str) -> str:
    slug = _SLUG_CLEANUP.sub("-", value.strip().lower()).strip("-")
    slug = re.sub("-{2,}", "-", slug)
    if not slug:
        raise InvariantViolationError("Не удалось построить slug из title.")
    return slug


def _ensure_admin_or_teacher(actor_roles: list[str]) -> None:
    role_set = {role.strip().lower() for role in actor_roles if role.strip()}
    if "admin" in role_set or "teacher" in role_set:
        return
    raise AccessDeniedError("Операция доступна только admin/teacher.")


def _resolve_display_name(
    *, payload_value: str | None, fallback_value: str | None
) -> str | None:
    payload_name = payload_value.strip() if payload_value else ""
    if payload_name:
        return payload_name
    fallback_name = fallback_value.strip() if fallback_value else ""
    return fallback_name or None


class CreateCourseHandler:
    """Создает курс."""

    def __init__(
        self,
        *,
        repository: CourseRepository,
        clock: Clock,
        teacher_directory: TeacherDirectory,
    ) -> None:
        self._repository = repository
        self._clock = clock
        self._teacher_directory = teacher_directory

    def __call__(self, command: CreateCourseCommand) -> CourseResult:
        _ensure_admin_or_teacher(command.actor_roles)
        role_set = {
            role.strip().lower() for role in command.actor_roles if role.strip()
        }
        if (
            "teacher" in role_set
            and "admin" not in role_set
            and command.teacher_id != command.actor_id
        ):
            raise AccessDeniedError("teacher может создавать курс только для себя.")

        teacher = self._teacher_directory.get_teacher(command.teacher_id)
        if teacher is None:
            raise InvariantViolationError(
                "teacher_id не найден в users_service или не имеет роли teacher."
            )

        slug = command.slug.strip() if command.slug else _slugify(command.title)
        existing = self._repository.get_by_slug(slug)
        if existing is not None:
            raise InvariantViolationError("Курс с таким slug уже существует.")

        seo_title = (command.seo_meta_title or command.title).strip()
        seo_description = (
            command.seo_meta_description or command.description or command.title
        ).strip()
        if len(seo_description) > 160:
            seo_description = seo_description[:160]

        course = Course.create(
            course_id=str(uuid4()),
            title=command.title,
            description=command.description,
            teacher_id=command.teacher_id,
            teacher_display_name=_resolve_display_name(
                payload_value=command.teacher_display_name,
                fallback_value=teacher.display_name,
            ),
            slug=CourseSlug(slug),
            schedule=CourseSchedule(
                starts_at=command.starts_at,
                duration_days=command.duration_days,
                enrollment_opens_at=command.enrollment_opens_at,
                enrollment_closes_at=command.enrollment_closes_at,
                access_ttl_days=command.access_ttl_days,
                timezone=command.timezone,
            ),
            pricing=CoursePricing(price=command.price, currency=command.currency),
            audience=CourseAudience(
                language=command.language,
                level=command.level,
                age_min=command.age_min,
                age_max=command.age_max,
                max_students=command.max_students,
            ),
            delivery=CourseDeliverySettings(
                tags=tuple(command.tags),
                cover_image_url=command.cover_image_url,
                is_live_enabled=command.is_live_enabled,
                live_room_template_id=command.live_room_template_id,
            ),
            seo=SeoMetadata(
                meta_title=seo_title,
                meta_description=seo_description,
                canonical_url=command.seo_canonical_url,
                robots=command.seo_robots,
                og_image_url=command.seo_og_image_url,
            ),
            created_at=self._clock.now(),
            created_by=command.actor_id,
        )
        self._repository.save(course)
        return to_course_result(course)


class UpdateCourseHandler:
    """Обновляет курс."""

    def __init__(
        self,
        *,
        repository: CourseRepository,
        clock: Clock,
        teacher_directory: TeacherDirectory,
    ) -> None:
        self._repository = repository
        self._clock = clock
        self._teacher_directory = teacher_directory

    def __call__(self, command: UpdateCourseCommand) -> CourseResult:
        _ensure_admin_or_teacher(command.actor_roles)
        course = self._repository.get(command.course_id)
        if course is None:
            raise NotFoundError("Курс не найден.")

        role_set = {
            role.strip().lower() for role in command.actor_roles if role.strip()
        }
        if "admin" not in role_set and course.teacher_id != command.actor_id:
            raise AccessDeniedError(
                "Обновлять курс может только его teacher_owner или admin."
            )

        if command.slug is not None:
            target_slug = command.slug.strip()
            existing = self._repository.get_by_slug(target_slug)
            if existing is not None and existing.course_id != course.course_id:
                raise InvariantViolationError("Курс с таким slug уже существует.")
            course.slug = CourseSlug(target_slug)

        if command.title is not None:
            course.title = command.title
        if command.description is not None:
            course.description = (
                command.description.strip() if command.description else None
            )
        resolved_teacher_display_name: str | None = None
        if command.teacher_id is not None:
            teacher = self._teacher_directory.get_teacher(command.teacher_id)
            if teacher is None:
                raise InvariantViolationError(
                    "teacher_id не найден в users_service или не имеет роли teacher."
                )
            course.teacher_id = command.teacher_id
            resolved_teacher_display_name = teacher.display_name
        if command.teacher_display_name is not None:
            course.teacher_display_name = _resolve_display_name(
                payload_value=command.teacher_display_name,
                fallback_value=resolved_teacher_display_name,
            )
        elif resolved_teacher_display_name is not None:
            course.teacher_display_name = resolved_teacher_display_name

        course.schedule = CourseSchedule(
            starts_at=command.starts_at or course.schedule.starts_at,
            duration_days=command.duration_days or course.schedule.duration_days,
            enrollment_opens_at=(
                command.enrollment_opens_at
                if command.enrollment_opens_at is not None
                else course.schedule.enrollment_opens_at
            ),
            enrollment_closes_at=(
                command.enrollment_closes_at
                if command.enrollment_closes_at is not None
                else course.schedule.enrollment_closes_at
            ),
            access_ttl_days=(
                command.access_ttl_days
                if command.access_ttl_days is not None
                else course.schedule.access_ttl_days
            ),
            timezone=command.timezone or course.schedule.timezone,
        )
        course.pricing = CoursePricing(
            price=command.price if command.price is not None else course.pricing.price,
            currency=command.currency or course.pricing.currency,
        )
        course.audience = CourseAudience(
            language=command.language or course.audience.language,
            level=command.level or course.audience.level,
            age_min=(
                command.age_min
                if command.age_min is not None
                else course.audience.age_min
            ),
            age_max=(
                command.age_max
                if command.age_max is not None
                else course.audience.age_max
            ),
            max_students=(
                command.max_students
                if command.max_students is not None
                else course.audience.max_students
            ),
        )
        course.delivery = CourseDeliverySettings(
            tags=(
                tuple(command.tags)
                if command.tags is not None
                else course.delivery.tags
            ),
            cover_image_url=(
                command.cover_image_url
                if command.cover_image_url is not None
                else course.delivery.cover_image_url
            ),
            is_live_enabled=(
                command.is_live_enabled
                if command.is_live_enabled is not None
                else course.delivery.is_live_enabled
            ),
            live_room_template_id=(
                command.live_room_template_id
                if command.live_room_template_id is not None
                else course.delivery.live_room_template_id
            ),
        )
        course.seo = SeoMetadata(
            meta_title=command.seo_meta_title or course.seo.meta_title,
            meta_description=command.seo_meta_description
            or course.seo.meta_description,
            canonical_url=(
                command.seo_canonical_url
                if command.seo_canonical_url is not None
                else course.seo.canonical_url
            ),
            robots=command.seo_robots or course.seo.robots,
            og_image_url=(
                command.seo_og_image_url
                if command.seo_og_image_url is not None
                else course.seo.og_image_url
            ),
        )

        course.meta.touch(at=self._clock.now(), actor_id=command.actor_id)
        self._repository.save(course)
        return to_course_result(course)


class GetCourseByIdHandler:
    """Возвращает курс по ID."""

    def __init__(self, *, repository: CourseRepository) -> None:
        self._repository = repository

    def __call__(self, query: GetCourseByIdQuery) -> CourseResult:
        _ensure_admin_or_teacher(query.actor_roles)
        course = self._repository.get(query.course_id)
        if course is None:
            raise NotFoundError("Курс не найден.")

        role_set = {role.strip().lower() for role in query.actor_roles if role.strip()}
        if "admin" not in role_set and course.teacher_id != query.actor_id:
            raise AccessDeniedError("Просмотр курса разрешен только owner/admin.")
        return to_course_result(course)


class AddModuleHandler:
    """Добавляет модуль в курс."""

    def __init__(self, *, repository: CourseRepository, clock: Clock) -> None:
        self._repository = repository
        self._clock = clock

    def __call__(self, command: AddModuleCommand) -> CourseResult:
        _ensure_admin_or_teacher(command.actor_roles)
        course = self._repository.get(command.course_id)
        if course is None:
            raise NotFoundError("Курс не найден.")

        role_set = {
            role.strip().lower() for role in command.actor_roles if role.strip()
        }
        if "admin" not in role_set and course.teacher_id != command.actor_id:
            raise AccessDeniedError("Добавлять модули может только owner/admin.")

        module = Module.create(
            module_id=(command.module_id or str(uuid4())),
            title=command.title,
            description=command.description,
            is_required=command.is_required,
            released_at=command.released_at,
            created_at=self._clock.now(),
            created_by=command.actor_id,
        )
        course.add_module(
            module, changed_at=self._clock.now(), changed_by=command.actor_id
        )
        self._repository.save(course)
        return to_course_result(course)


class AddLessonHandler:
    """Добавляет урок в модуль курса."""

    def __init__(self, *, repository: CourseRepository, clock: Clock) -> None:
        self._repository = repository
        self._clock = clock

    def __call__(self, command: AddLessonCommand) -> CourseResult:
        _ensure_admin_or_teacher(command.actor_roles)
        course = self._repository.get(command.course_id)
        if course is None:
            raise NotFoundError("Курс не найден.")

        role_set = {
            role.strip().lower() for role in command.actor_roles if role.strip()
        }
        if "admin" not in role_set and course.teacher_id != command.actor_id:
            raise AccessDeniedError("Добавлять уроки может только owner/admin.")

        module = next(
            (m for m in course.modules if m.module_id == command.module_id), None
        )
        if module is None:
            raise NotFoundError("Модуль не найден.")

        lesson = Lesson.create(
            lesson_id=(command.lesson_id or str(uuid4())),
            title=command.title,
            description=command.description,
            content_type=command.content_type,
            content_ref=command.content_ref,
            duration_minutes=command.duration_minutes,
            is_preview=command.is_preview,
            released_at=command.released_at,
            created_at=self._clock.now(),
            created_by=command.actor_id,
        )
        module.add_lesson(
            lesson,
            changed_at=self._clock.now(),
            changed_by=command.actor_id,
        )
        course.meta.touch(at=self._clock.now(), actor_id=command.actor_id)
        self._repository.save(course)
        return to_course_result(course)


class PublishCourseHandler:
    """Публикует курс."""

    def __init__(self, *, repository: CourseRepository, clock: Clock) -> None:
        self._repository = repository
        self._clock = clock

    def __call__(self, command: PublishCourseCommand) -> CourseResult:
        _ensure_admin_or_teacher(command.actor_roles)
        course = self._repository.get(command.course_id)
        if course is None:
            raise NotFoundError("Курс не найден.")

        role_set = {
            role.strip().lower() for role in command.actor_roles if role.strip()
        }
        if "admin" not in role_set and course.teacher_id != command.actor_id:
            raise AccessDeniedError("Публиковать курс может только owner/admin.")

        course.publish(changed_at=self._clock.now(), changed_by=command.actor_id)
        self._repository.save(course)
        return to_course_result(course)


class ArchiveCourseHandler:
    """Архивирует курс."""

    def __init__(self, *, repository: CourseRepository, clock: Clock) -> None:
        self._repository = repository
        self._clock = clock

    def __call__(self, command: ArchiveCourseCommand) -> CourseResult:
        _ensure_admin_or_teacher(command.actor_roles)
        course = self._repository.get(command.course_id)
        if course is None:
            raise NotFoundError("Курс не найден.")

        role_set = {
            role.strip().lower() for role in command.actor_roles if role.strip()
        }
        if "admin" not in role_set and course.teacher_id != command.actor_id:
            raise AccessDeniedError("Архивировать курс может только owner/admin.")

        course.archive(changed_at=self._clock.now(), changed_by=command.actor_id)
        self._repository.save(course)
        return to_course_result(course)


class UpdateModuleHandler:
    """Обновляет модуль курса."""

    def __init__(self, *, repository: CourseRepository, clock: Clock) -> None:
        self._repository = repository
        self._clock = clock

    def __call__(self, command: UpdateModuleCommand) -> CourseResult:
        _ensure_admin_or_teacher(command.actor_roles)
        course = self._repository.get(command.course_id)
        if course is None:
            raise NotFoundError("Курс не найден.")
        role_set = {
            role.strip().lower() for role in command.actor_roles if role.strip()
        }
        if "admin" not in role_set and course.teacher_id != command.actor_id:
            raise AccessDeniedError("Обновлять модуль может только owner/admin.")
        module = next(
            (m for m in course.modules if m.module_id == command.module_id), None
        )
        if module is None:
            raise NotFoundError("Модуль не найден.")
        module.update(
            title=command.title,
            description=command.description,
            is_required=command.is_required,
            released_at=command.released_at,
            status=command.status,
            changed_at=self._clock.now(),
            changed_by=command.actor_id,
        )
        course.meta.touch(at=self._clock.now(), actor_id=command.actor_id)
        self._repository.save(course)
        return to_course_result(course)


class UpdateLessonHandler:
    """Обновляет урок курса."""

    def __init__(self, *, repository: CourseRepository, clock: Clock) -> None:
        self._repository = repository
        self._clock = clock

    def __call__(self, command: UpdateLessonCommand) -> CourseResult:
        _ensure_admin_or_teacher(command.actor_roles)
        course = self._repository.get(command.course_id)
        if course is None:
            raise NotFoundError("Курс не найден.")
        role_set = {
            role.strip().lower() for role in command.actor_roles if role.strip()
        }
        if "admin" not in role_set and course.teacher_id != command.actor_id:
            raise AccessDeniedError("Обновлять урок может только owner/admin.")
        module = next(
            (m for m in course.modules if m.module_id == command.module_id), None
        )
        if module is None:
            raise NotFoundError("Модуль не найден.")
        lesson = next(
            (l for l in module.lessons if l.lesson_id == command.lesson_id), None
        )
        if lesson is None:
            raise NotFoundError("Урок не найден.")
        lesson.update(
            title=command.title,
            description=command.description,
            content_type=command.content_type,
            content_ref=command.content_ref,
            duration_minutes=command.duration_minutes,
            is_preview=command.is_preview,
            released_at=command.released_at,
            status=command.status,
            changed_at=self._clock.now(),
            changed_by=command.actor_id,
        )
        module.meta.touch(at=self._clock.now(), actor_id=command.actor_id)
        course.meta.touch(at=self._clock.now(), actor_id=command.actor_id)
        self._repository.save(course)
        return to_course_result(course)
