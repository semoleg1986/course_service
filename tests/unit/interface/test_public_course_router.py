from __future__ import annotations

import os

from fastapi.testclient import TestClient

from src.interface.http.app import create_app
from src.interface.http.common.actor import HttpActor
from src.interface.http.observability import reset_metrics
from src.interface.http.v1.admin.router import get_http_actor
from src.interface.http.wiring import get_runtime


def _client_with_admin() -> TestClient:
    os.environ["COURSE_USE_INMEMORY"] = "1"
    reset_metrics()
    get_runtime.cache_clear()
    app = create_app()
    app.dependency_overrides[get_http_actor] = lambda: HttpActor(
        actor_id="admin-1",
        roles=["admin"],
    )
    return TestClient(app)


def test_public_course_returns_published_course_with_viewer_timezone() -> None:
    client = _client_with_admin()

    create_response = client.post(
        "/v1/admin/courses",
        json={
            "title": "Public Course",
            "teacher_id": "teacher-1",
            "starts_at": "2026-09-01T16:00:00+09:00",
            "duration_days": 30,
            "enrollment_opens_at": "2026-08-01T10:00:00+09:00",
            "enrollment_closes_at": "2026-08-20T18:00:00+09:00",
            "timezone": "Asia/Yakutsk",
            "slug": "public-course",
        },
    )
    assert create_response.status_code == 201, create_response.text
    course_id = create_response.json()["course_id"]

    module_response = client.post(
        f"/v1/admin/courses/{course_id}/modules",
        json={"module_id": "module-public-1", "title": "Module 1"},
    )
    assert module_response.status_code == 200, module_response.text

    lesson_response = client.post(
        f"/v1/admin/courses/{course_id}/modules/module-public-1/lessons",
        json={"lesson_id": "lesson-public-1", "title": "Lesson 1"},
    )
    assert lesson_response.status_code == 200, lesson_response.text

    module_publish_response = client.patch(
        f"/v1/admin/courses/{course_id}/modules/module-public-1",
        json={"status": "published"},
    )
    assert module_publish_response.status_code == 200, module_publish_response.text

    lesson_publish_response = client.patch(
        f"/v1/admin/courses/{course_id}/modules/module-public-1/lessons/lesson-public-1",
        json={"status": "published"},
    )
    assert lesson_publish_response.status_code == 200, lesson_publish_response.text

    publish_response = client.post(f"/v1/admin/courses/{course_id}/publish")
    assert publish_response.status_code == 200, publish_response.text

    public_response = client.get(
        "/v1/public/courses/public-course?viewer_timezone=Asia/Tbilisi"
    )
    assert public_response.status_code == 200, public_response.text
    body = public_response.json()
    assert body["slug"] == "public-course"
    assert body["publish_state"] == "published"
    assert body["viewer_timezone"] == "Asia/Tbilisi"
    assert body["starts_at_local"] == "2026-09-01T11:00:00+04:00"
    assert body["enrollment_opens_at_local"] == "2026-08-01T05:00:00+04:00"
    assert body["enrollment_closes_at_local"] == "2026-08-20T13:00:00+04:00"
    assert body["modules"] == [
        {
            "module_id": "module-public-1",
            "title": "Module 1",
            "lessons_count": 1,
        }
    ]

    metrics = client.get("/metrics")
    assert metrics.status_code == 200
    assert 'public_course_requests_total{result="success"} 1' in metrics.text


def test_public_course_hides_non_published_course() -> None:
    client = _client_with_admin()

    create_response = client.post(
        "/v1/admin/courses",
        json={
            "title": "Draft Course",
            "teacher_id": "teacher-1",
            "starts_at": "2026-09-01T09:00:00Z",
            "duration_days": 30,
            "slug": "draft-course",
        },
    )
    assert create_response.status_code == 201, create_response.text

    public_response = client.get("/v1/public/courses/draft-course")
    assert public_response.status_code == 404, public_response.text

    metrics = client.get("/metrics")
    assert metrics.status_code == 200
    assert 'public_course_requests_total{result="not_found"} 1' in metrics.text


def test_public_course_rejects_invalid_viewer_timezone() -> None:
    client = _client_with_admin()

    create_response = client.post(
        "/v1/admin/courses",
        json={
            "title": "Bad Timezone Course",
            "teacher_id": "teacher-1",
            "starts_at": "2026-09-01T09:00:00Z",
            "duration_days": 30,
            "slug": "bad-timezone-course",
        },
    )
    assert create_response.status_code == 201, create_response.text
    course_id = create_response.json()["course_id"]

    module_response = client.post(
        f"/v1/admin/courses/{course_id}/modules",
        json={"module_id": "module-public-2", "title": "Module 2"},
    )
    assert module_response.status_code == 200, module_response.text

    lesson_response = client.post(
        f"/v1/admin/courses/{course_id}/modules/module-public-2/lessons",
        json={"lesson_id": "lesson-public-2", "title": "Lesson 2"},
    )
    assert lesson_response.status_code == 200, lesson_response.text

    module_publish_response = client.patch(
        f"/v1/admin/courses/{course_id}/modules/module-public-2",
        json={"status": "published"},
    )
    assert module_publish_response.status_code == 200, module_publish_response.text

    lesson_publish_response = client.patch(
        f"/v1/admin/courses/{course_id}/modules/module-public-2/lessons/lesson-public-2",
        json={"status": "published"},
    )
    assert lesson_publish_response.status_code == 200, lesson_publish_response.text

    publish_response = client.post(f"/v1/admin/courses/{course_id}/publish")
    assert publish_response.status_code == 200, publish_response.text

    public_response = client.get(
        "/v1/public/courses/bad-timezone-course?viewer_timezone=Bad/Timezone"
    )
    assert public_response.status_code == 422, public_response.text
    assert (
        "viewer_timezone должен быть корректным IANA timezone"
        in public_response.json()["detail"]
    )
