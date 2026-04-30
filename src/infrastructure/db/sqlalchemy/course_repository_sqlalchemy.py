"""SQLAlchemy репозиторий курса."""

from __future__ import annotations

from sqlalchemy import delete, select
from sqlalchemy.orm import Session, sessionmaker

from src.domain.content.course.entity import Course, Lesson, Module
from src.domain.content.course.value_objects import (
    CourseAudience,
    CourseDeliverySettings,
    CoursePricing,
    CourseSchedule,
    CourseSlug,
    SeoMetadata,
)
from src.domain.shared.entity import EntityMeta
from src.domain.shared.statuses import PublishState
from src.infrastructure.db.sqlalchemy.models import (
    CourseCatalogModel,
    CourseLessonModel,
    CourseModuleModel,
)


class SqlalchemyCourseRepository:
    """Реализация CourseRepository поверх SQLAlchemy."""

    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    def get(self, course_id: str) -> Course | None:
        with self._session_factory() as db:
            model = db.get(CourseCatalogModel, course_id)
            return self._to_entity_with_children(model) if model else None

    def get_by_slug(self, slug: str) -> Course | None:
        with self._session_factory() as db:
            stmt = select(CourseCatalogModel).where(CourseCatalogModel.slug == slug)
            model = db.execute(stmt).scalar_one_or_none()
            return self._to_entity_with_children(model) if model else None

    def save(self, course: Course) -> None:
        with self._session_factory.begin() as db:
            model = db.get(CourseCatalogModel, course.course_id)
            if model is None:
                model = CourseCatalogModel(course_id=course.course_id)
                db.add(model)
            self._copy_to_model(course, model)
            db.execute(
                delete(CourseLessonModel).where(
                    CourseLessonModel.module_id.in_(
                        select(CourseModuleModel.module_id).where(
                            CourseModuleModel.course_id == course.course_id
                        )
                    )
                )
            )
            db.execute(
                delete(CourseModuleModel).where(
                    CourseModuleModel.course_id == course.course_id
                )
            )
            for module_position, module in enumerate(course.modules, start=1):
                module_model = CourseModuleModel(
                    module_id=module.module_id,
                    course_id=course.course_id,
                    title=module.title,
                    position=module_position,
                    created_at=module.meta.created_at,
                    created_by=module.meta.created_by,
                    updated_at=module.meta.updated_at,
                    updated_by=module.meta.updated_by,
                    version=module.meta.version,
                )
                db.add(module_model)
                for lesson_position, lesson in enumerate(module.lessons, start=1):
                    lesson_model = CourseLessonModel(
                        lesson_id=lesson.lesson_id,
                        module_id=module.module_id,
                        title=lesson.title,
                        position=lesson_position,
                        created_at=lesson.meta.created_at,
                        created_by=lesson.meta.created_by,
                        updated_at=lesson.meta.updated_at,
                        updated_by=lesson.meta.updated_by,
                        version=lesson.meta.version,
                    )
                    db.add(lesson_model)

    @staticmethod
    def _copy_to_model(course: Course, model: CourseCatalogModel) -> None:
        model.title = course.title
        model.description = course.description
        model.teacher_id = course.teacher_id
        model.teacher_display_name = course.teacher_display_name
        model.slug = course.slug.value

        model.starts_at = course.schedule.starts_at
        model.duration_days = course.schedule.duration_days
        model.access_ttl_days = course.schedule.access_ttl_days
        model.enrollment_opens_at = course.schedule.enrollment_opens_at
        model.enrollment_closes_at = course.schedule.enrollment_closes_at
        model.timezone = course.schedule.timezone

        model.price = course.pricing.price
        model.currency = course.pricing.currency
        model.language = course.audience.language
        model.age_min = course.audience.age_min
        model.age_max = course.audience.age_max
        model.level = course.audience.level
        model.max_students = course.audience.max_students

        model.tags = list(course.delivery.tags)
        model.cover_image_url = course.delivery.cover_image_url
        model.is_live_enabled = course.delivery.is_live_enabled
        model.live_room_template_id = course.delivery.live_room_template_id

        model.publish_state = course.publish_state.value
        model.published_at = course.published_at
        model.published_by_admin_id = course.published_by_admin_id
        model.archived_at = course.archived_at
        model.archived_by = course.archived_by

        model.seo_meta_title = course.seo.meta_title
        model.seo_meta_description = course.seo.meta_description
        model.seo_canonical_url = course.seo.canonical_url
        model.seo_robots = course.seo.robots
        model.seo_og_image_url = course.seo.og_image_url

        model.created_at = course.meta.created_at
        model.created_by = course.meta.created_by
        model.updated_at = course.meta.updated_at
        model.updated_by = course.meta.updated_by
        model.version = course.meta.version

    @staticmethod
    def _to_entity(model: CourseCatalogModel) -> Course:
        course = Course(
            course_id=model.course_id,
            title=model.title,
            description=model.description,
            teacher_id=model.teacher_id,
            teacher_display_name=model.teacher_display_name,
            slug=CourseSlug(model.slug),
            schedule=CourseSchedule(
                starts_at=model.starts_at,
                duration_days=model.duration_days,
                enrollment_opens_at=model.enrollment_opens_at,
                enrollment_closes_at=model.enrollment_closes_at,
                access_ttl_days=model.access_ttl_days,
                timezone=model.timezone,
            ),
            pricing=CoursePricing(price=float(model.price), currency=model.currency),
            audience=CourseAudience(
                language=model.language,
                level=model.level,
                age_min=model.age_min,
                age_max=model.age_max,
                max_students=model.max_students,
            ),
            delivery=CourseDeliverySettings(
                tags=tuple(model.tags or []),
                cover_image_url=model.cover_image_url,
                is_live_enabled=model.is_live_enabled,
                live_room_template_id=model.live_room_template_id,
            ),
            seo=SeoMetadata(
                meta_title=model.seo_meta_title,
                meta_description=model.seo_meta_description,
                canonical_url=model.seo_canonical_url,
                robots=model.seo_robots,
                og_image_url=model.seo_og_image_url,
            ),
            meta=EntityMeta(
                version=model.version,
                created_at=model.created_at,
                created_by=model.created_by,
                updated_at=model.updated_at,
                updated_by=model.updated_by,
                archived_at=model.archived_at,
                archived_by=model.archived_by,
            ),
            publish_state=PublishState(model.publish_state),
            modules=[],
            published_at=model.published_at,
            published_by_admin_id=model.published_by_admin_id,
        )
        return course

    def _to_entity_with_children(self, model: CourseCatalogModel) -> Course:
        course = self._to_entity(model)
        with self._session_factory() as db:
            module_models = (
                db.execute(
                    select(CourseModuleModel)
                    .where(CourseModuleModel.course_id == course.course_id)
                    .order_by(CourseModuleModel.position.asc())
                )
                .scalars()
                .all()
            )
            for module_model in module_models:
                module = Module(
                    module_id=module_model.module_id,
                    title=module_model.title,
                    meta=EntityMeta(
                        version=module_model.version,
                        created_at=module_model.created_at,
                        created_by=module_model.created_by,
                        updated_at=module_model.updated_at,
                        updated_by=module_model.updated_by,
                    ),
                    lessons=[],
                )
                lesson_models = (
                    db.execute(
                        select(CourseLessonModel)
                        .where(CourseLessonModel.module_id == module_model.module_id)
                        .order_by(CourseLessonModel.position.asc())
                    )
                    .scalars()
                    .all()
                )
                for lesson_model in lesson_models:
                    lesson = Lesson(
                        lesson_id=lesson_model.lesson_id,
                        title=lesson_model.title,
                        meta=EntityMeta(
                            version=lesson_model.version,
                            created_at=lesson_model.created_at,
                            created_by=lesson_model.created_by,
                            updated_at=lesson_model.updated_at,
                            updated_by=lesson_model.updated_by,
                        ),
                    )
                    module.lessons.append(lesson)
                course.modules.append(module)
        return course
