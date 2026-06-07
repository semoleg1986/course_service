"""Handlers управления курсом."""

from __future__ import annotations

import re
from collections.abc import Callable
from uuid import uuid4

from src.application.common.dto import (
    AdminCourseListItemResult,
    AdminCourseListResult,
    CourseAuthoringResult,
    CourseResult,
    PublicCourseResult,
)
from src.application.common.mappers import (
    to_course_authoring_result,
    to_course_result,
    to_public_course_card_result,
    to_public_course_result,
)
from src.application.courses.commands.dto import (
    AddLessonCommand,
    AddModuleCommand,
    ArchiveCourseCommand,
    ArchiveLessonCommand,
    ArchiveModuleCommand,
    CreateCourseCommand,
    DuplicateLessonCommand,
    DuplicateModuleCommand,
    PublishCourseCommand,
    ReorderLessonsCommand,
    ReorderModulesCommand,
    UpdateCourseCommand,
    UpdateLessonCommand,
    UpdateModuleCommand,
)
from src.application.courses.queries.dto import (
    GetCourseAuthoringQuery,
    GetCourseByIdQuery,
    GetPublishedCourseBySlugQuery,
    ListAdminCoursesQuery,
    ListPublishedCoursesQuery,
)
from src.application.ports.audit_evidence import AuditEvidenceRecord
from src.application.ports.clock import Clock
from src.application.ports.course_admin_read_model import CourseAdminReadModel
from src.application.ports.teacher_directory import TeacherDirectory
from src.application.ports.unit_of_work import UnitOfWork
from src.domain.content.course.entity import Course, Lesson, Module
from src.domain.content.course.repository import CourseRepository
from src.domain.content.course.value_objects import (
    CourseAudience,
    CourseDeliverySettings,
    CourseSchedule,
    CourseSlug,
    SeoMetadata,
)
from src.domain.errors import AccessDeniedError, InvariantViolationError, NotFoundError
from src.domain.shared.statuses import PublishState

_SLUG_CLEANUP = re.compile(r"[^a-z0-9]+")
WriteUnitOfWorkFactory = Callable[[], UnitOfWork]


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


def _close_uow(uow: UnitOfWork) -> None:
    uow.close()


def _ensure_course_editor(
    *,
    course: Course,
    actor_id: str,
    actor_roles: list[str],
    action: str,
) -> None:
    role_set = {role.strip().lower() for role in actor_roles if role.strip()}
    if "admin" in role_set or course.teacher_id == actor_id:
        return
    raise AccessDeniedError(f"{action} может только owner/admin.")


def _ordered_item_ids(items: list, *, entity_name: str, id_field: str) -> list[str]:
    if not items:
        raise InvariantViolationError(f"reorder {entity_name} требует items.")
    positions = [item.position for item in items]
    if any(position < 1 for position in positions):
        raise InvariantViolationError("position должен быть >= 1.")
    if len(positions) != len(set(positions)):
        raise InvariantViolationError("Список position содержит дубликаты.")
    expected_positions = set(range(1, len(items) + 1))
    if set(positions) != expected_positions:
        raise InvariantViolationError("position должен быть непрерывным с 1.")
    return [
        getattr(item, id_field)
        for item in sorted(items, key=lambda item: item.position)
    ]


class CreateCourseHandler:
    """Создает курс."""

    def __init__(
        self,
        *,
        uow_factory: WriteUnitOfWorkFactory,
        clock: Clock,
        teacher_directory: TeacherDirectory,
    ) -> None:
        self._uow_factory = uow_factory
        self._clock = clock
        self._teacher_directory = teacher_directory

    def __call__(self, command: CreateCourseCommand) -> CourseResult:
        uow = self._uow_factory()
        try:
            repository = uow.repositories.courses
            read_model = uow.repositories.access_read_model
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
            existing = repository.get_by_slug(slug)
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
            repository.save(course)
            read_model.seed_course_owner(course.course_id, course.teacher_id)
            uow.commit()
            return to_course_result(course)
        except Exception:
            uow.rollback()
            raise
        finally:
            _close_uow(uow)


class UpdateCourseHandler:
    """Обновляет курс."""

    def __init__(
        self,
        *,
        uow_factory: WriteUnitOfWorkFactory,
        clock: Clock,
        teacher_directory: TeacherDirectory,
    ) -> None:
        self._uow_factory = uow_factory
        self._clock = clock
        self._teacher_directory = teacher_directory

    def __call__(self, command: UpdateCourseCommand) -> CourseResult:
        uow = self._uow_factory()
        try:
            repository = uow.repositories.courses
            read_model = uow.repositories.access_read_model
            _ensure_admin_or_teacher(command.actor_roles)
            course = repository.get(command.course_id)
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
                existing = repository.get_by_slug(target_slug)
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
                        "teacher_id не найден в users_service "
                        "или не имеет роли teacher."
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
            repository.save(course)
            read_model.seed_course_owner(course.course_id, course.teacher_id)
            uow.commit()
            return to_course_result(course)
        except Exception:
            uow.rollback()
            raise
        finally:
            _close_uow(uow)


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


class GetCourseAuthoringHandler:
    """Возвращает полный admin/studio read model курса."""

    def __init__(self, *, repository: CourseRepository) -> None:
        self._repository = repository

    def __call__(self, query: GetCourseAuthoringQuery) -> CourseAuthoringResult:
        _ensure_admin_or_teacher(query.actor_roles)
        course = self._repository.get(query.course_id)
        if course is None:
            raise NotFoundError("Курс не найден.")

        role_set = {role.strip().lower() for role in query.actor_roles if role.strip()}
        if "admin" not in role_set and course.teacher_id != query.actor_id:
            raise AccessDeniedError("Просмотр курса разрешен только owner/admin.")
        return to_course_authoring_result(course)


class ListAdminCoursesHandler:
    """Возвращает admin/studio список курсов."""

    def __init__(self, *, read_model: CourseAdminReadModel) -> None:
        self._read_model = read_model

    def __call__(self, query: ListAdminCoursesQuery) -> AdminCourseListResult:
        _ensure_admin_or_teacher(query.actor_roles)
        role_set = {role.strip().lower() for role in query.actor_roles if role.strip()}
        publish_state = query.publish_state.strip() if query.publish_state else None
        if publish_state is not None:
            try:
                publish_state = PublishState(publish_state).value
            except ValueError as exc:
                raise InvariantViolationError("publish_state некорректен.") from exc

        effective_teacher_id = query.teacher_id.strip() if query.teacher_id else None
        if "admin" not in role_set:
            if (
                effective_teacher_id is not None
                and effective_teacher_id != query.actor_id
            ):
                raise AccessDeniedError(
                    "teacher может смотреть только список своих курсов."
                )
            effective_teacher_id = query.actor_id

        records, total = self._read_model.list_admin_courses(
            publish_state=publish_state,
            teacher_id=effective_teacher_id,
            search=query.search,
            limit=query.limit,
            offset=query.offset,
        )
        return AdminCourseListResult(
            items=[
                AdminCourseListItemResult(
                    course_id=record.course_id,
                    title=record.title,
                    teacher_id=record.teacher_id,
                    teacher_display_name=record.teacher_display_name,
                    slug=record.slug,
                    publish_state=record.publish_state,
                    modules_count=record.modules_count,
                    lessons_total=record.lessons_total,
                    published_at=record.published_at,
                    archived_at=record.archived_at,
                    created_at=record.created_at,
                    created_by=record.created_by,
                    updated_at=record.updated_at,
                    updated_by=record.updated_by,
                    version=record.version,
                )
                for record in records
            ],
            total=total,
            limit=query.limit,
            offset=query.offset,
        )


class GetPublishedCourseBySlugHandler:
    """Возвращает опубликованный курс по slug."""

    def __init__(self, *, repository: CourseRepository) -> None:
        self._repository = repository

    def __call__(self, query: GetPublishedCourseBySlugQuery) -> PublicCourseResult:
        course = self._repository.get_by_slug(query.slug)
        if course is None or course.publish_state != PublishState.PUBLISHED:
            raise NotFoundError("Опубликованный курс не найден.")
        return to_public_course_result(course)


class ListPublishedCoursesHandler:
    """Возвращает public catalog опубликованных курсов."""

    def __init__(self, *, repository: CourseRepository) -> None:
        self._repository = repository

    def __call__(self, query: ListPublishedCoursesQuery) -> list[dict]:
        courses = self._repository.list_published(
            limit=query.limit,
            offset=query.offset,
        )
        return [to_public_course_card_result(course) for course in courses]


class AddModuleHandler:
    """Добавляет модуль в курс."""

    def __init__(self, *, uow_factory: WriteUnitOfWorkFactory, clock: Clock) -> None:
        self._uow_factory = uow_factory
        self._clock = clock

    def __call__(self, command: AddModuleCommand) -> CourseResult:
        uow = self._uow_factory()
        try:
            repository = uow.repositories.courses
            _ensure_admin_or_teacher(command.actor_roles)
            course = repository.get(command.course_id)
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
            repository.save(course)
            uow.commit()
            return to_course_result(course)
        except Exception:
            uow.rollback()
            raise
        finally:
            _close_uow(uow)


class AddLessonHandler:
    """Добавляет урок в модуль курса."""

    def __init__(self, *, uow_factory: WriteUnitOfWorkFactory, clock: Clock) -> None:
        self._uow_factory = uow_factory
        self._clock = clock

    def __call__(self, command: AddLessonCommand) -> CourseResult:
        uow = self._uow_factory()
        try:
            repository = uow.repositories.courses
            _ensure_admin_or_teacher(command.actor_roles)
            course = repository.get(command.course_id)
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
            repository.save(course)
            uow.commit()
            return to_course_result(course)
        except Exception:
            uow.rollback()
            raise
        finally:
            _close_uow(uow)


class PublishCourseHandler:
    """Публикует курс."""

    def __init__(
        self,
        *,
        uow_factory: WriteUnitOfWorkFactory,
        clock: Clock,
    ) -> None:
        self._uow_factory = uow_factory
        self._clock = clock

    def __call__(self, command: PublishCourseCommand) -> CourseResult:
        uow = self._uow_factory()
        try:
            repository = uow.repositories.courses
            audit_repo = uow.repositories.audit_evidence
            _ensure_admin_or_teacher(command.actor_roles)
            course = repository.get(command.course_id)
            if course is None:
                raise NotFoundError("Курс не найден.")

            role_set = {
                role.strip().lower() for role in command.actor_roles if role.strip()
            }
            if "admin" not in role_set and course.teacher_id != command.actor_id:
                reason = "Публиковать курс может только owner/admin."
                audit_repo.append(
                    AuditEvidenceRecord(
                        audit_id=str(uuid4()),
                        action="course.publish",
                        occurred_at=self._clock.now(),
                        result="denied",
                        actor_id=command.actor_id,
                        actor_roles=tuple(command.actor_roles),
                        target_type="course",
                        target_id=course.course_id,
                        reason=reason,
                        reason_code="course_publish_forbidden",
                        request_id=command.request_id,
                        correlation_id=command.correlation_id,
                        course_id=course.course_id,
                    )
                )
                uow.commit()
                raise AccessDeniedError(reason)

            course.publish(changed_at=self._clock.now(), changed_by=command.actor_id)
            repository.save(course)
            uow.commit()
            return to_course_result(course)
        except AccessDeniedError:
            raise
        except Exception:
            uow.rollback()
            raise
        finally:
            _close_uow(uow)


class ArchiveCourseHandler:
    """Архивирует курс."""

    def __init__(
        self,
        *,
        uow_factory: WriteUnitOfWorkFactory,
        clock: Clock,
    ) -> None:
        self._uow_factory = uow_factory
        self._clock = clock

    def __call__(self, command: ArchiveCourseCommand) -> CourseResult:
        uow = self._uow_factory()
        try:
            repository = uow.repositories.courses
            audit_repo = uow.repositories.audit_evidence
            _ensure_admin_or_teacher(command.actor_roles)
            course = repository.get(command.course_id)
            if course is None:
                raise NotFoundError("Курс не найден.")

            role_set = {
                role.strip().lower() for role in command.actor_roles if role.strip()
            }
            if "admin" not in role_set and course.teacher_id != command.actor_id:
                reason = "Архивировать курс может только owner/admin."
                audit_repo.append(
                    AuditEvidenceRecord(
                        audit_id=str(uuid4()),
                        action="course.archive",
                        occurred_at=self._clock.now(),
                        result="denied",
                        actor_id=command.actor_id,
                        actor_roles=tuple(command.actor_roles),
                        target_type="course",
                        target_id=course.course_id,
                        reason=reason,
                        reason_code="course_archive_forbidden",
                        request_id=command.request_id,
                        correlation_id=command.correlation_id,
                        course_id=course.course_id,
                    )
                )
                uow.commit()
                raise AccessDeniedError(reason)

            course.archive(changed_at=self._clock.now(), changed_by=command.actor_id)
            repository.save(course)
            uow.commit()
            return to_course_result(course)
        except AccessDeniedError:
            raise
        except Exception:
            uow.rollback()
            raise
        finally:
            _close_uow(uow)


class UpdateModuleHandler:
    """Обновляет модуль курса."""

    def __init__(self, *, uow_factory: WriteUnitOfWorkFactory, clock: Clock) -> None:
        self._uow_factory = uow_factory
        self._clock = clock

    def __call__(self, command: UpdateModuleCommand) -> CourseResult:
        uow = self._uow_factory()
        try:
            repository = uow.repositories.courses
            _ensure_admin_or_teacher(command.actor_roles)
            course = repository.get(command.course_id)
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
            repository.save(course)
            uow.commit()
            return to_course_result(course)
        except Exception:
            uow.rollback()
            raise
        finally:
            _close_uow(uow)


class UpdateLessonHandler:
    """Обновляет урок курса."""

    def __init__(self, *, uow_factory: WriteUnitOfWorkFactory, clock: Clock) -> None:
        self._uow_factory = uow_factory
        self._clock = clock

    def __call__(self, command: UpdateLessonCommand) -> CourseResult:
        uow = self._uow_factory()
        try:
            repository = uow.repositories.courses
            _ensure_admin_or_teacher(command.actor_roles)
            course = repository.get(command.course_id)
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
                (
                    item
                    for item in module.lessons
                    if item.lesson_id == command.lesson_id
                ),
                None,
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
            repository.save(course)
            uow.commit()
            return to_course_result(course)
        except Exception:
            uow.rollback()
            raise
        finally:
            _close_uow(uow)


class ArchiveModuleHandler:
    """Архивирует модуль курса."""

    def __init__(self, *, uow_factory: WriteUnitOfWorkFactory, clock: Clock) -> None:
        self._uow_factory = uow_factory
        self._clock = clock

    def __call__(self, command: ArchiveModuleCommand) -> CourseResult:
        uow = self._uow_factory()
        try:
            repository = uow.repositories.courses
            _ensure_admin_or_teacher(command.actor_roles)
            course = repository.get(command.course_id)
            if course is None:
                raise NotFoundError("Курс не найден.")
            _ensure_course_editor(
                course=course,
                actor_id=command.actor_id,
                actor_roles=command.actor_roles,
                action="Архивировать модуль",
            )
            course.archive_module(
                module_id=command.module_id,
                changed_at=self._clock.now(),
                changed_by=command.actor_id,
            )
            repository.save(course)
            uow.commit()
            return to_course_result(course)
        except Exception:
            uow.rollback()
            raise
        finally:
            _close_uow(uow)


class ArchiveLessonHandler:
    """Архивирует урок курса."""

    def __init__(self, *, uow_factory: WriteUnitOfWorkFactory, clock: Clock) -> None:
        self._uow_factory = uow_factory
        self._clock = clock

    def __call__(self, command: ArchiveLessonCommand) -> CourseResult:
        uow = self._uow_factory()
        try:
            repository = uow.repositories.courses
            _ensure_admin_or_teacher(command.actor_roles)
            course = repository.get(command.course_id)
            if course is None:
                raise NotFoundError("Курс не найден.")
            _ensure_course_editor(
                course=course,
                actor_id=command.actor_id,
                actor_roles=command.actor_roles,
                action="Архивировать урок",
            )
            course.archive_lesson(
                module_id=command.module_id,
                lesson_id=command.lesson_id,
                changed_at=self._clock.now(),
                changed_by=command.actor_id,
            )
            repository.save(course)
            uow.commit()
            return to_course_result(course)
        except Exception:
            uow.rollback()
            raise
        finally:
            _close_uow(uow)


class ReorderModulesHandler:
    """Переупорядочивает модули курса."""

    def __init__(self, *, uow_factory: WriteUnitOfWorkFactory, clock: Clock) -> None:
        self._uow_factory = uow_factory
        self._clock = clock

    def __call__(self, command: ReorderModulesCommand) -> CourseResult:
        uow = self._uow_factory()
        try:
            repository = uow.repositories.courses
            _ensure_admin_or_teacher(command.actor_roles)
            course = repository.get(command.course_id)
            if course is None:
                raise NotFoundError("Курс не найден.")
            _ensure_course_editor(
                course=course,
                actor_id=command.actor_id,
                actor_roles=command.actor_roles,
                action="Переупорядочивать модули",
            )
            course.reorder_modules(
                ordered_module_ids=_ordered_item_ids(
                    command.items,
                    entity_name="modules",
                    id_field="module_id",
                ),
                changed_at=self._clock.now(),
                changed_by=command.actor_id,
            )
            repository.save(course)
            uow.commit()
            return to_course_result(course)
        except Exception:
            uow.rollback()
            raise
        finally:
            _close_uow(uow)


class DuplicateModuleHandler:
    """Дублирует модуль курса."""

    def __init__(self, *, uow_factory: WriteUnitOfWorkFactory, clock: Clock) -> None:
        self._uow_factory = uow_factory
        self._clock = clock

    def __call__(self, command: DuplicateModuleCommand) -> CourseResult:
        uow = self._uow_factory()
        try:
            repository = uow.repositories.courses
            _ensure_admin_or_teacher(command.actor_roles)
            course = repository.get(command.course_id)
            if course is None:
                raise NotFoundError("Курс не найден.")
            _ensure_course_editor(
                course=course,
                actor_id=command.actor_id,
                actor_roles=command.actor_roles,
                action="Дублировать модуль",
            )
            source = next(
                (
                    item
                    for item in course.modules
                    if item.module_id == command.module_id
                ),
                None,
            )
            if source is None:
                raise NotFoundError("Модуль не найден.")
            course.duplicate_module(
                module_id=command.module_id,
                new_module_id=str(uuid4()),
                new_lesson_ids=[str(uuid4()) for _ in source.lessons],
                changed_at=self._clock.now(),
                changed_by=command.actor_id,
            )
            repository.save(course)
            uow.commit()
            return to_course_result(course)
        except Exception:
            uow.rollback()
            raise
        finally:
            _close_uow(uow)


class ReorderLessonsHandler:
    """Переупорядочивает уроки модуля курса."""

    def __init__(self, *, uow_factory: WriteUnitOfWorkFactory, clock: Clock) -> None:
        self._uow_factory = uow_factory
        self._clock = clock

    def __call__(self, command: ReorderLessonsCommand) -> CourseResult:
        uow = self._uow_factory()
        try:
            repository = uow.repositories.courses
            _ensure_admin_or_teacher(command.actor_roles)
            course = repository.get(command.course_id)
            if course is None:
                raise NotFoundError("Курс не найден.")
            _ensure_course_editor(
                course=course,
                actor_id=command.actor_id,
                actor_roles=command.actor_roles,
                action="Переупорядочивать уроки",
            )
            module = next(
                (
                    item
                    for item in course.modules
                    if item.module_id == command.module_id
                ),
                None,
            )
            if module is None:
                raise NotFoundError("Модуль не найден.")
            module.reorder_lessons(
                ordered_lesson_ids=_ordered_item_ids(
                    command.items,
                    entity_name="lessons",
                    id_field="lesson_id",
                ),
                changed_at=self._clock.now(),
                changed_by=command.actor_id,
            )
            course.meta.touch(at=self._clock.now(), actor_id=command.actor_id)
            repository.save(course)
            uow.commit()
            return to_course_result(course)
        except Exception:
            uow.rollback()
            raise
        finally:
            _close_uow(uow)


class DuplicateLessonHandler:
    """Дублирует урок курса."""

    def __init__(self, *, uow_factory: WriteUnitOfWorkFactory, clock: Clock) -> None:
        self._uow_factory = uow_factory
        self._clock = clock

    def __call__(self, command: DuplicateLessonCommand) -> CourseResult:
        uow = self._uow_factory()
        try:
            repository = uow.repositories.courses
            _ensure_admin_or_teacher(command.actor_roles)
            course = repository.get(command.course_id)
            if course is None:
                raise NotFoundError("Курс не найден.")
            _ensure_course_editor(
                course=course,
                actor_id=command.actor_id,
                actor_roles=command.actor_roles,
                action="Дублировать урок",
            )
            course.duplicate_lesson(
                module_id=command.module_id,
                lesson_id=command.lesson_id,
                new_lesson_id=str(uuid4()),
                changed_at=self._clock.now(),
                changed_by=command.actor_id,
            )
            repository.save(course)
            uow.commit()
            return to_course_result(course)
        except Exception:
            uow.rollback()
            raise
        finally:
            _close_uow(uow)
