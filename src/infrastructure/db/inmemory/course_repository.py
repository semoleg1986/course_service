"""In-memory репозиторий курсов."""

from __future__ import annotations

from src.domain.content.course.entity import Course


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

    def save(self, course: Course) -> None:
        self._by_id[course.course_id] = course
