"""In-memory CourseOfferCatalog adapter."""

from __future__ import annotations


class InMemoryCourseOfferCatalog:
    """Local adapter that keeps authoring tests independent from catalog service."""

    def __init__(self, *, default_has_offer: bool = True) -> None:
        self._default_has_offer = default_has_offer
        self._course_statuses: dict[str, bool] = {}

    def seed_course_offer_status(self, course_id: str, has_offer: bool) -> None:
        """Override offer status for a specific course."""

        self._course_statuses[course_id] = has_offer

    def has_active_default_offer(self, course_id: str) -> bool:
        return self._course_statuses.get(course_id, self._default_has_offer)
