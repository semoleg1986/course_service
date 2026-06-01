"""In-memory репозиторий курсов."""

from __future__ import annotations

from src.application.ports.course_admin_read_model import CourseAdminListRecord
from src.domain.content.course.entity import Course
from src.domain.shared.statuses import PublishState


class InMemoryCourseRepository:
    """In-memory реализация CourseRepository."""

    def __init__(self) -> None:
        self._by_id: dict[str, Course] = {}

    def get(self, course_id: str) -> Course | None:
        return self._by_id.get(course_id)

    def get_by_slug(self, slug: str) -> Course | None:
        for item in self._by_id.values():
            if item.slug.value == slug:
                return item
        return None

    def list_published(self, *, limit: int = 100, offset: int = 0) -> list[Course]:
        items = [
            item
            for item in self._by_id.values()
            if item.publish_state == PublishState.PUBLISHED
        ]
        items.sort(
            key=lambda item: (
                item.published_at is None,
                item.published_at,
                item.meta.created_at,
            ),
            reverse=True,
        )
        return items[offset : offset + limit]

    def list_admin_courses(
        self,
        *,
        publish_state: str | None = None,
        teacher_id: str | None = None,
        search: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[list[CourseAdminListRecord], int]:
        items = list(self._by_id.values())
        if publish_state is not None:
            items = [
                item for item in items if item.publish_state.value == publish_state
            ]
        if teacher_id is not None:
            items = [item for item in items if item.teacher_id == teacher_id]
        if search:
            needle = search.strip().lower()
            items = [
                item
                for item in items
                if needle in item.title.lower() or needle in item.slug.value.lower()
            ]
        items.sort(key=lambda item: item.meta.updated_at, reverse=True)
        total = len(items)
        return (
            [
                CourseAdminListRecord(
                    course_id=item.course_id,
                    title=item.title,
                    teacher_id=item.teacher_id,
                    teacher_display_name=item.teacher_display_name,
                    slug=item.slug.value,
                    publish_state=item.publish_state.value,
                    price=item.pricing.price,
                    currency=item.pricing.currency,
                    modules_count=item.modules_count,
                    lessons_total=item.lessons_total,
                    published_at=item.published_at,
                    archived_at=item.archived_at,
                    created_at=item.meta.created_at,
                    created_by=item.meta.created_by,
                    updated_at=item.meta.updated_at,
                    updated_by=item.meta.updated_by,
                    version=item.meta.version,
                )
                for item in items[offset : offset + limit]
            ],
            total,
        )

    def save(self, course: Course) -> None:
        self._by_id[course.course_id] = course
