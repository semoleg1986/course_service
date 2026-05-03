from __future__ import annotations

import json

from src.infrastructure.users.users_service_parent_student_relation_checker import (
    UsersServiceParentStudentRelationChecker,
)
from src.infrastructure.users.users_service_teacher_directory import (
    UsersServiceTeacherDirectory,
)
from src.interface.http import observability


class _FakeResponse:
    def __init__(self, payload: dict[str, object]) -> None:
        self._payload = json.dumps(payload).encode("utf-8")

    def read(self) -> bytes:
        return self._payload

    def __enter__(self) -> "_FakeResponse":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None


def test_users_service_adapters_forward_correlation_id(
    monkeypatch,
) -> None:  # noqa: ANN001
    captured: dict[str, dict[str, str]] = {}

    def _fake_urlopen(request, timeout: float = 2.0):  # noqa: ANN001
        captured[request.full_url] = dict(request.header_items())
        if "/teachers/" in request.full_url:
            return _FakeResponse(
                {
                    "teacher_id": "teacher-1",
                    "display_name": "Teacher One",
                    "status": "active",
                    "roles": ["teacher"],
                }
            )
        return _FakeResponse({"has_relation": True})

    monkeypatch.setattr(
        "src.infrastructure.users.users_service_teacher_directory.urlopen",
        _fake_urlopen,
    )
    monkeypatch.setattr(
        "src.infrastructure.users.users_service_parent_student_relation_checker.urlopen",
        _fake_urlopen,
    )

    request_token = observability._CURRENT_REQUEST_ID.set("req-course-001")
    correlation_token = observability._CURRENT_CORRELATION_ID.set("corr-course-001")
    try:
        teacher = UsersServiceTeacherDirectory(
            base_url="http://users-service:8002",
            service_token="svc-token",
            timeout_seconds=2.0,
        ).get_teacher("teacher-1")
        relation = UsersServiceParentStudentRelationChecker(
            base_url="http://users-service:8002",
            service_token="svc-token",
            timeout_seconds=2.0,
        ).has_relation("parent-1", "student-1")
    finally:
        observability._CURRENT_REQUEST_ID.reset(request_token)
        observability._CURRENT_CORRELATION_ID.reset(correlation_token)

    assert teacher is not None
    assert teacher.teacher_id == "teacher-1"
    assert relation is True
    for headers in captured.values():
        assert headers["X-correlation-id"] == "corr-course-001"
