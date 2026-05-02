from __future__ import annotations

import os

from fastapi.testclient import TestClient

from src.interface.http.app import create_app
from src.interface.http.common.actor import HttpActor, get_http_actor
from src.interface.http.observability import reset_metrics
from src.interface.http.wiring import get_runtime


def _client_with_actor(actor_id: str, roles: list[str]) -> TestClient:
    os.environ["COURSE_USE_INMEMORY"] = "1"
    reset_metrics()
    get_runtime.cache_clear()
    app = create_app()
    app.dependency_overrides[get_http_actor] = lambda: HttpActor(
        actor_id=actor_id, roles=roles
    )
    return TestClient(app)


def test_parent_progress_happy_path_with_pagination_and_filter() -> None:
    client = _client_with_actor("parent-1", ["parent"])

    response = client.get(
        "/v1/parent/students/student-1/courses/progress?limit=20&offset=0&status=active"
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["limit"] == 20
    assert body["offset"] == 0
    assert body["status"] == "active"
    assert len(body["items"]) == 1
    assert body["items"][0]["course_id"] == "00000000-0000-0000-0000-000000000001"

    page_2 = client.get(
        "/v1/parent/students/student-1/courses/progress?limit=1&offset=1"
    )
    assert page_2.status_code == 200, page_2.text
    assert page_2.json()["items"] == []

    metrics = client.get("/metrics")
    assert metrics.status_code == 200
    assert (
        'parent_progress_requests_total{result="success",status_filter="active"} 1'
        in metrics.text
    )
    assert (
        'parent_progress_requests_total{result="success",status_filter="all"} 1'
        in metrics.text
    )


def test_parent_progress_forbidden_for_unrelated_parent() -> None:
    client = _client_with_actor("parent-2", ["parent"])

    response = client.get("/v1/parent/students/student-1/courses/progress")
    assert response.status_code == 403, response.text

    metrics = client.get("/metrics")
    assert metrics.status_code == 200
    assert 'parent_acl_denied_total{endpoint="progress"} 1' in metrics.text


def test_parent_completed_courses_endpoint() -> None:
    client = _client_with_actor("parent-1", ["parent"])

    response = client.get(
        "/v1/parent/students/student-1/courses/completed?limit=10&offset=0&viewer_timezone=Asia/Tbilisi"
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["limit"] == 10
    assert body["offset"] == 0
    assert body["viewer_timezone"] == "Asia/Tbilisi"
    assert isinstance(body["items"], list)
    if body["items"]:
        assert body["items"][0]["completed_at_local"] is not None

    metrics = client.get("/metrics")
    assert metrics.status_code == 200
    assert 'parent_completed_requests_total{result="success"} 1' in metrics.text


def test_parent_progress_accepts_viewer_timezone() -> None:
    client = _client_with_actor("parent-1", ["parent"])

    response = client.get(
        "/v1/parent/students/student-1/courses/progress?viewer_timezone=Asia/Tbilisi"
    )
    assert response.status_code == 200, response.text
    assert response.json()["viewer_timezone"] == "Asia/Tbilisi"


def test_parent_progress_rejects_invalid_viewer_timezone() -> None:
    client = _client_with_actor("parent-1", ["parent"])

    response = client.get(
        "/v1/parent/students/student-1/courses/progress?viewer_timezone=Bad/Timezone"
    )
    assert response.status_code == 422, response.text
    assert (
        "viewer_timezone должен быть корректным IANA timezone"
        in response.json()["detail"]
    )


def test_parent_progress_requires_bearer_token() -> None:
    os.environ["COURSE_USE_INMEMORY"] = "1"
    reset_metrics()
    get_runtime.cache_clear()
    client = TestClient(create_app())

    response = client.get("/v1/parent/students/student-1/courses/progress")
    assert response.status_code == 401, response.text
