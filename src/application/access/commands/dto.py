"""Command DTO для обработки access event."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ApplyAccessGrantedEventCommand:
    """Применяет событие course.access.granted к projection."""

    event_id: str
    course_id: str
    student_id: str
    granted_status: str = "approved"
