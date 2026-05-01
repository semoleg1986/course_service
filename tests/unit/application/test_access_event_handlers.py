from src.application.access.commands.dto import ApplyAccessGrantedEventCommand
from src.application.access.handlers.access_event_handlers import (
    ApplyAccessGrantedEventHandler,
)
from src.infrastructure.db.inmemory.access_read_model import InMemoryAccessReadModel


def test_apply_access_granted_event_handler_deduplicates_by_event_id() -> None:
    read_model = InMemoryAccessReadModel()
    handler = ApplyAccessGrantedEventHandler(read_model=read_model)

    first = handler(
        ApplyAccessGrantedEventCommand(
            event_id="evt-1",
            course_id="course-1",
            student_id="student-1",
            granted_status="approved",
        )
    )
    second = handler(
        ApplyAccessGrantedEventCommand(
            event_id="evt-1",
            course_id="course-1",
            student_id="student-1",
            granted_status="approved",
        )
    )

    assert first is True
    assert second is False
    assert read_model.get_access_grant_status("course-1", "student-1") == "approved"
