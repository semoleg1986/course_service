"""Handlers применения access events."""

from __future__ import annotations

from src.application.access.commands.dto import ApplyAccessGrantedEventCommand
from src.application.ports.access_read_model import AccessReadModel


class ApplyAccessGrantedEventHandler:
    """Применяет событие выдачи доступа к read-model с dedup по event_id."""

    def __init__(self, *, read_model: AccessReadModel) -> None:
        self._read_model = read_model

    def __call__(self, command: ApplyAccessGrantedEventCommand) -> bool:
        return self._read_model.apply_access_granted_event(
            event_id=command.event_id,
            course_id=command.course_id,
            student_id=command.student_id,
            granted_status=command.granted_status,
        )
