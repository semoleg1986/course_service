"""Read model port for admin/studio course lists."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol


@dataclass(frozen=True, slots=True)
class CourseAdminListRecord:
    """Storage-level row for admin/studio course lists."""

    course_id: str
    title: str
    teacher_id: str
    teacher_display_name: str | None
    slug: str
    publish_state: str
    price: float
    currency: str
    modules_count: int
    lessons_total: int
    published_at: datetime | None
    archived_at: datetime | None
    created_at: datetime
    created_by: str
    updated_at: datetime
    updated_by: str
    version: int


class CourseAdminReadModel(Protocol):
    """Optimized read model for admin/studio course lists."""

    def list_admin_courses(
        self,
        *,
        publish_state: str | None = None,
        teacher_id: str | None = None,
        search: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[list[CourseAdminListRecord], int]:
        """Return paginated course list records and total count."""
