from __future__ import annotations

import os

from fastapi.testclient import TestClient

from src.interface.http.app import create_app
from src.interface.http.common.actor import HttpActor
from src.interface.http.v1.internal.router import get_http_actor
from src.interface.http.wiring import get_runtime


def test_internal_check_by_token_route() -> None:
    os.environ["COURSE_USE_INMEMORY"] = "1"
    get_runtime.cache_clear()

    app = create_app()
    app.dependency_overrides[get_http_actor] = lambda: HttpActor(actor_id="student-1", roles=["student"])
    client = TestClient(app)

    response = client.post(
        "/internal/v1/access/check-by-token",
        json={
            "course_id": "course-1",
            "student_id": "student-1",
            "require_active_grant": True,
            "require_enrollment": True,
        },
    )
    assert response.status_code == 200
    assert response.json()["decision"] in {"allow", "deny"}
