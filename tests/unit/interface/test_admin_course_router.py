from __future__ import annotations

import os

from fastapi.testclient import TestClient

from src.interface.http.app import create_app
from src.interface.http.common.actor import HttpActor
from src.interface.http.common.rate_limit import reset_rate_limiter
from src.interface.http.v1.admin.router import get_http_actor
from src.interface.http.wiring import get_runtime


def _client_with_actor(actor_id: str, roles: list[str]) -> TestClient:
    os.environ["COURSE_USE_INMEMORY"] = "1"
    reset_rate_limiter()
    get_runtime.cache_clear()
    app = create_app()
    app.dependency_overrides[get_http_actor] = lambda: HttpActor(
        actor_id=actor_id, roles=roles
    )
    return TestClient(app)


def test_admin_create_update_get_course_flow() -> None:
    client = _client_with_actor("admin-1", ["admin"])

    create_response = client.post(
        "/v1/admin/courses",
        json={
            "title": "Алгебра 8 класс",
            "description": "Базовый курс алгебры",
            "teacher_id": "teacher-1",
            "teacher_display_name": "Иван Иванов",
            "starts_at": "2026-09-01T09:00:00Z",
            "duration_days": 120,
            "access_ttl_days": 180,
            "enrollment_opens_at": "2026-08-01T00:00:00Z",
            "enrollment_closes_at": "2026-09-10T00:00:00Z",
            "price": 1990,
            "currency": "USD",
            "language": "ru",
            "age_min": 12,
            "age_max": 16,
            "level": "intermediate",
            "tags": ["algebra", "school"],
            "cover_image_url": "https://cdn.example.com/courses/algebra-8.png",
            "is_live_enabled": True,
            "live_room_template_id": "room-template-1",
            "timezone": "Asia/Bishkek",
            "max_students": 30,
            "slug": "algebra-8",
            "seo": {
                "meta_title": "Алгебра 8 класс",
                "meta_description": "Курс алгебры для 8 класса",
                "robots": "index",
            },
        },
    )
    assert create_response.status_code == 201, create_response.text
    created = create_response.json()
    assert created["course_id"]
    assert created["teacher_id"] == "teacher-1"
    assert created["modules_count"] == 0
    assert created["estimated_duration_hours"] == 0
    assert created["is_free"] is False
    runtime = get_runtime()
    assert (
        runtime.access_read_model.get_course_owner(created["course_id"]) == "teacher-1"
    )

    course_id = created["course_id"]

    update_response = client.patch(
        f"/v1/admin/courses/{course_id}",
        json={
            "title": "Алгебра 8 класс (обновлено)",
            "price": 0,
            "tags": ["algebra", "updated"],
        },
    )
    assert update_response.status_code == 200, update_response.text
    updated = update_response.json()
    assert updated["title"] == "Алгебра 8 класс (обновлено)"
    assert updated["price"] == 0
    assert updated["is_free"] is True
    assert updated["tags"] == ["algebra", "updated"]
    assert runtime.access_read_model.get_course_owner(course_id) == "teacher-1"

    get_response = client.get(f"/v1/admin/courses/{course_id}")
    assert get_response.status_code == 200, get_response.text
    fetched = get_response.json()
    assert fetched["course_id"] == course_id
    assert fetched["teacher_display_name"] == "Иван Иванов"

    publish_without_structure = client.post(f"/v1/admin/courses/{course_id}/publish")
    assert publish_without_structure.status_code == 400

    add_module = client.post(
        f"/v1/admin/courses/{course_id}/modules",
        json={"module_id": "module-1", "title": "Модуль 1"},
    )
    assert add_module.status_code == 200, add_module.text
    assert add_module.json()["modules_count"] == 1

    publish_without_lessons = client.post(f"/v1/admin/courses/{course_id}/publish")
    assert publish_without_lessons.status_code == 400

    add_lesson = client.post(
        f"/v1/admin/courses/{course_id}/modules/module-1/lessons",
        json={"lesson_id": "lesson-1", "title": "Урок 1"},
    )
    assert add_lesson.status_code == 200, add_lesson.text
    assert add_lesson.json()["lessons_total"] == 1

    publish_still_blocked = client.post(f"/v1/admin/courses/{course_id}/publish")
    assert publish_still_blocked.status_code == 400

    module_publish = client.patch(
        f"/v1/admin/courses/{course_id}/modules/module-1",
        json={"status": "published"},
    )
    assert module_publish.status_code == 200, module_publish.text

    lesson_publish = client.patch(
        f"/v1/admin/courses/{course_id}/modules/module-1/lessons/lesson-1",
        json={"status": "published", "duration_minutes": 45, "content_type": "video"},
    )
    assert lesson_publish.status_code == 200, lesson_publish.text

    publish_ok = client.post(f"/v1/admin/courses/{course_id}/publish")
    assert publish_ok.status_code == 200, publish_ok.text
    assert publish_ok.json()["publish_state"] == "published"

    archive_ok = client.post(f"/v1/admin/courses/{course_id}/archive")
    assert archive_ok.status_code == 200, archive_ok.text
    assert archive_ok.json()["publish_state"] == "archived"


def test_teacher_can_create_only_for_self() -> None:
    client = _client_with_actor("teacher-22", ["teacher"])

    response = client.post(
        "/v1/admin/courses",
        json={
            "title": "Геометрия",
            "teacher_id": "teacher-99",
            "starts_at": "2026-09-01T09:00:00Z",
            "duration_days": 90,
        },
    )
    assert response.status_code == 403


def test_admin_create_rejects_unknown_teacher() -> None:
    client = _client_with_actor("admin-1", ["admin"])

    response = client.post(
        "/v1/admin/courses",
        json={
            "title": "Физика",
            "teacher_id": "unknown-teacher",
            "starts_at": "2026-09-01T09:00:00Z",
            "duration_days": 90,
        },
    )
    assert response.status_code == 400
    assert "teacher_id не найден" in response.json()["detail"]


def test_admin_create_course_rejects_naive_starts_at() -> None:
    client = _client_with_actor("admin-1", ["admin"])

    response = client.post(
        "/v1/admin/courses",
        json={
            "title": "Химия",
            "teacher_id": "teacher-1",
            "starts_at": "2026-09-01T09:00:00",
            "duration_days": 90,
        },
    )
    assert response.status_code == 422
    assert "starts_at должен содержать timezone offset" in response.json()["detail"]


def test_admin_update_course_rejects_naive_enrollment_dates() -> None:
    client = _client_with_actor("admin-1", ["admin"])

    create_response = client.post(
        "/v1/admin/courses",
        json={
            "title": "Biology",
            "teacher_id": "teacher-1",
            "starts_at": "2026-09-01T09:00:00Z",
            "duration_days": 90,
        },
    )
    assert create_response.status_code == 201, create_response.text
    course_id = create_response.json()["course_id"]

    update_response = client.patch(
        f"/v1/admin/courses/{course_id}",
        json={"enrollment_opens_at": "2026-08-01T00:00:00"},
    )
    assert update_response.status_code == 422
    assert (
        "enrollment_opens_at должен содержать timezone offset"
        in update_response.json()["detail"]
    )


def test_admin_get_course_supports_viewer_timezone_projection() -> None:
    client = _client_with_actor("admin-1", ["admin"])

    create_response = client.post(
        "/v1/admin/courses",
        json={
            "title": "Timezone Course",
            "teacher_id": "teacher-1",
            "starts_at": "2026-09-01T16:00:00+09:00",
            "duration_days": 30,
            "enrollment_opens_at": "2026-08-01T10:00:00+09:00",
            "enrollment_closes_at": "2026-08-20T18:00:00+09:00",
            "timezone": "Asia/Yakutsk",
            "slug": "timezone-course",
        },
    )
    assert create_response.status_code == 201, create_response.text
    course_id = create_response.json()["course_id"]

    get_response = client.get(
        f"/v1/admin/courses/{course_id}?viewer_timezone=Asia/Tbilisi"
    )
    assert get_response.status_code == 200, get_response.text
    payload = get_response.json()
    assert payload["viewer_timezone"] == "Asia/Tbilisi"
    assert payload["starts_at_local"] == "2026-09-01T11:00:00+04:00"
    assert payload["enrollment_opens_at_local"] == "2026-08-01T05:00:00+04:00"
    assert payload["enrollment_closes_at_local"] == "2026-08-20T13:00:00+04:00"


def test_admin_get_course_rejects_invalid_viewer_timezone() -> None:
    client = _client_with_actor("admin-1", ["admin"])

    create_response = client.post(
        "/v1/admin/courses",
        json={
            "title": "Viewer TZ Course",
            "teacher_id": "teacher-1",
            "starts_at": "2026-09-01T09:00:00Z",
            "duration_days": 30,
            "slug": "viewer-tz-course",
        },
    )
    assert create_response.status_code == 201, create_response.text
    course_id = create_response.json()["course_id"]

    get_response = client.get(
        f"/v1/admin/courses/{course_id}?viewer_timezone=Bad/Timezone"
    )
    assert get_response.status_code == 422
    assert (
        "viewer_timezone должен быть корректным IANA timezone"
        in get_response.json()["detail"]
    )


def test_admin_update_course_resyncs_owner_projection_when_teacher_changes() -> None:
    client = _client_with_actor("admin-1", ["admin"])

    create_response = client.post(
        "/v1/admin/courses",
        json={
            "title": "Teacher Reassign",
            "teacher_id": "teacher-1",
            "starts_at": "2026-09-01T09:00:00Z",
            "duration_days": 30,
        },
    )
    assert create_response.status_code == 201, create_response.text
    course_id = create_response.json()["course_id"]
    runtime = get_runtime()
    assert runtime.access_read_model.get_course_owner(course_id) == "teacher-1"

    update_response = client.patch(
        f"/v1/admin/courses/{course_id}",
        json={"teacher_id": "teacher-22"},
    )
    assert update_response.status_code == 200, update_response.text
    assert runtime.access_read_model.get_course_owner(course_id) == "teacher-22"


def test_teacher_cannot_publish_other_teacher_course_and_denial_is_retained() -> None:
    os.environ["COURSE_USE_INMEMORY"] = "1"
    get_runtime.cache_clear()
    app = create_app()
    actor_state = {"actor_id": "admin-1", "roles": ["admin"]}
    app.dependency_overrides[get_http_actor] = lambda: HttpActor(
        actor_id=actor_state["actor_id"],
        roles=actor_state["roles"],
    )
    client = TestClient(app)

    create_response = client.post(
        "/v1/admin/courses",
        json={
            "title": "Protected Course",
            "teacher_id": "teacher-1",
            "starts_at": "2026-09-01T09:00:00Z",
            "duration_days": 30,
        },
    )
    assert create_response.status_code == 201, create_response.text
    course_id = create_response.json()["course_id"]

    actor_state["actor_id"] = "teacher-22"
    actor_state["roles"] = ["teacher"]
    denied = client.post(
        f"/v1/admin/courses/{course_id}/publish",
        headers={
            "X-Request-ID": "req-course-publish-denied-1",
            "X-Correlation-ID": "corr-course-publish-denied-1",
        },
    )
    assert denied.status_code == 403

    runtime = get_runtime()
    records = runtime.audit_repo.list_all()
    assert len(records) >= 1
    record = records[-1]
    assert record.action == "course.publish"
    assert record.result == "denied"
    assert record.course_id == course_id
    assert record.request_id == "req-course-publish-denied-1"
    assert record.correlation_id == "corr-course-publish-denied-1"
    assert record.reason_code == "course_publish_forbidden"


def test_teacher_cannot_archive_other_teacher_course_and_denial_is_retained() -> None:
    os.environ["COURSE_USE_INMEMORY"] = "1"
    get_runtime.cache_clear()
    app = create_app()
    actor_state = {"actor_id": "admin-1", "roles": ["admin"]}
    app.dependency_overrides[get_http_actor] = lambda: HttpActor(
        actor_id=actor_state["actor_id"],
        roles=actor_state["roles"],
    )
    client = TestClient(app)

    create_response = client.post(
        "/v1/admin/courses",
        json={
            "title": "Protected Archive Course",
            "teacher_id": "teacher-1",
            "starts_at": "2026-09-01T09:00:00Z",
            "duration_days": 30,
        },
    )
    assert create_response.status_code == 201, create_response.text
    course_id = create_response.json()["course_id"]

    actor_state["actor_id"] = "teacher-22"
    actor_state["roles"] = ["teacher"]
    denied = client.post(
        f"/v1/admin/courses/{course_id}/archive",
        headers={
            "X-Request-ID": "req-course-archive-denied-1",
            "X-Correlation-ID": "corr-course-archive-denied-1",
        },
    )
    assert denied.status_code == 403

    runtime = get_runtime()
    records = runtime.audit_repo.list_all()
    assert len(records) >= 1
    record = records[-1]
    assert record.action == "course.archive"
    assert record.result == "denied"
    assert record.course_id == course_id
    assert record.request_id == "req-course-archive-denied-1"
    assert record.correlation_id == "corr-course-archive-denied-1"
    assert record.reason_code == "course_archive_forbidden"


def test_admin_publish_is_rate_limited(monkeypatch) -> None:
    monkeypatch.setenv("COURSE_RATE_LIMIT_ADMIN_PUBLISH_MAX", "1")
    monkeypatch.setenv("COURSE_RATE_LIMIT_ADMIN_PUBLISH_WINDOW_SECONDS", "60")
    client = _client_with_actor("admin-1", ["admin"])

    first_create = client.post(
        "/v1/admin/courses",
        json={
            "title": "RL Publish Course 1",
            "teacher_id": "teacher-1",
            "starts_at": "2026-09-01T09:00:00Z",
            "duration_days": 30,
        },
    )
    second_create = client.post(
        "/v1/admin/courses",
        json={
            "title": "RL Publish Course 2",
            "teacher_id": "teacher-1",
            "starts_at": "2026-09-01T09:00:00Z",
            "duration_days": 30,
        },
    )
    assert first_create.status_code == 201, first_create.text
    assert second_create.status_code == 201, second_create.text

    first_course_id = first_create.json()["course_id"]
    second_course_id = second_create.json()["course_id"]

    first_publish = client.post(
        f"/v1/admin/courses/{first_course_id}/publish",
        headers={"X-Request-ID": "req-course-rl-admin-publish-ok"},
    )
    assert first_publish.status_code in {200, 400}, first_publish.text

    second_publish = client.post(
        f"/v1/admin/courses/{second_course_id}/publish",
        headers={
            "X-Request-ID": "req-course-rl-admin-publish-1",
            "X-Correlation-ID": "corr-course-rl-admin-publish-1",
        },
    )
    assert second_publish.status_code == 429, second_publish.text
    assert (
        second_publish.json()["detail"]["detail"]
        == "Слишком много запросов, попробуйте позже."
    )


def test_admin_archive_is_rate_limited(monkeypatch) -> None:
    monkeypatch.setenv("COURSE_RATE_LIMIT_ADMIN_ARCHIVE_MAX", "1")
    monkeypatch.setenv("COURSE_RATE_LIMIT_ADMIN_ARCHIVE_WINDOW_SECONDS", "60")
    client = _client_with_actor("admin-1", ["admin"])

    first_create = client.post(
        "/v1/admin/courses",
        json={
            "title": "RL Archive Course 1",
            "teacher_id": "teacher-1",
            "starts_at": "2026-09-01T09:00:00Z",
            "duration_days": 30,
        },
    )
    second_create = client.post(
        "/v1/admin/courses",
        json={
            "title": "RL Archive Course 2",
            "teacher_id": "teacher-1",
            "starts_at": "2026-09-01T09:00:00Z",
            "duration_days": 30,
        },
    )
    assert first_create.status_code == 201, first_create.text
    assert second_create.status_code == 201, second_create.text

    first_archive = client.post(
        f"/v1/admin/courses/{first_create.json()['course_id']}/archive",
        headers={"X-Request-ID": "req-course-rl-admin-archive-ok"},
    )
    assert first_archive.status_code in {200, 400}, first_archive.text

    second_archive = client.post(
        f"/v1/admin/courses/{second_create.json()['course_id']}/archive",
        headers={
            "X-Request-ID": "req-course-rl-admin-archive-1",
            "X-Correlation-ID": "corr-course-rl-admin-archive-1",
        },
    )
    assert second_archive.status_code == 429, second_archive.text
    assert (
        second_archive.json()["detail"]["detail"]
        == "Слишком много запросов, попробуйте позже."
    )
