"""Port for course offer availability in commercial catalog."""

from __future__ import annotations

from typing import Protocol


class CourseOfferCatalog(Protocol):
    """Read-only commercial catalog contract used by authoring readiness."""

    def has_active_default_offer(self, course_id: str) -> bool:
        """Return whether a course has an active default offer."""
