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
    assert "price" not in created
    assert "currency" not in created
    assert "is_free" not in created
    runtime = get_runtime()
    assert (
        runtime.access_read_model.get_course_owner(created["course_id"]) == "teacher-1"
    )

    course_id = created["course_id"]

    update_response = client.patch(
        f"/v1/admin/courses/{course_id}",
        json={
            "title": "Алгебра 8 класс (обновлено)",
            "tags": ["algebra", "updated"],
        },
    )
    assert update_response.status_code == 200, update_response.text
    updated = update_response.json()
    assert updated["title"] == "Алгебра 8 класс (обновлено)"
    assert "price" not in updated
    assert "currency" not in updated
    assert "is_free" not in updated
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


def test_admin_authoring_read_model_returns_modules_and_lessons() -> None:
    client = _client_with_actor("admin-1", ["admin"])

    create_response = client.post(
        "/v1/admin/courses",
        json={
            "title": "Studio Course",
            "teacher_id": "teacher-1",
            "starts_at": "2026-09-01T09:00:00Z",
            "duration_days": 30,
            "slug": "studio-course",
        },
    )
    assert create_response.status_code == 201, create_response.text
    course_id = create_response.json()["course_id"]

    add_module = client.post(
        f"/v1/admin/courses/{course_id}/modules",
        json={
            "module_id": "studio-module-1",
            "title": "Module 1",
            "description": "Authoring module",
            "is_required": True,
        },
    )
    assert add_module.status_code == 200, add_module.text

    add_lesson = client.post(
        f"/v1/admin/courses/{course_id}/modules/studio-module-1/lessons",
        json={
            "lesson_id": "studio-lesson-1",
            "title": "Lesson 1",
            "description": "Authoring lesson",
            "content_type": "video",
            "content_ref": "https://cdn.example.com/lesson-1.mp4",
            "duration_minutes": 12,
            "is_preview": True,
        },
    )
    assert add_lesson.status_code == 200, add_lesson.text

    response = client.get(f"/v1/admin/courses/{course_id}/authoring")
    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["course"]["course_id"] == course_id
    assert payload["course"]["modules_count"] == 1
    assert payload["modules"][0]["module_id"] == "studio-module-1"
    assert payload["modules"][0]["position"] == 1
    assert payload["modules"][0]["lessons_count"] == 1
    assert payload["modules"][0]["lessons"][0]["lesson_id"] == "studio-lesson-1"
    assert payload["modules"][0]["lessons"][0]["position"] == 1
    assert payload["modules"][0]["lessons"][0]["content_ref"].endswith("lesson-1.mp4")
    assert payload["modules"][0]["created_by"] == "admin-1"
    assert payload["modules"][0]["updated_by"] == "admin-1"
    assert payload["modules"][0]["lessons"][0]["created_by"] == "admin-1"
    assert payload["modules"][0]["lessons"][0]["updated_by"] == "admin-1"
    assert payload["readiness"]["ready_to_publish"] is False
    readiness_codes = {
        check["code"]: check["passed"] for check in payload["readiness"]["checks"]
    }
    assert readiness_codes["has_default_offer"] is True
    assert payload["has_unpublished_changes"] is True
    assert payload["draft_version"] == payload["version"]


def test_admin_authoring_reorder_archive_and_readiness_flow() -> None:
    client = _client_with_actor("admin-1", ["admin"])

    create_response = client.post(
        "/v1/admin/courses",
        json={
            "title": "Builder Course",
            "teacher_id": "teacher-1",
            "starts_at": "2026-09-01T09:00:00Z",
            "duration_days": 30,
            "slug": "builder-course",
        },
    )
    assert create_response.status_code == 201, create_response.text
    course_id = create_response.json()["course_id"]

    for module_id in ["module-a", "module-b"]:
        response = client.post(
            f"/v1/admin/courses/{course_id}/modules",
            json={"module_id": module_id, "title": module_id},
        )
        assert response.status_code == 200, response.text

    for lesson_id in ["lesson-a", "lesson-b"]:
        response = client.post(
            f"/v1/admin/courses/{course_id}/modules/module-a/lessons",
            json={"lesson_id": lesson_id, "title": lesson_id},
        )
        assert response.status_code == 200, response.text

    reorder_modules = client.post(
        f"/v1/admin/courses/{course_id}/modules/reorder",
        json={
            "items": [
                {"module_id": "module-b", "position": 1},
                {"module_id": "module-a", "position": 2},
            ]
        },
    )
    assert reorder_modules.status_code == 200, reorder_modules.text

    reorder_lessons = client.post(
        f"/v1/admin/courses/{course_id}/modules/module-a/lessons/reorder",
        json={
            "items": [
                {"lesson_id": "lesson-b", "position": 1},
                {"lesson_id": "lesson-a", "position": 2},
            ]
        },
    )
    assert reorder_lessons.status_code == 200, reorder_lessons.text

    duplicate_reorder = client.post(
        f"/v1/admin/courses/{course_id}/modules/reorder",
        json={
            "items": [
                {"module_id": "module-b", "position": 1},
                {"module_id": "module-b", "position": 2},
            ]
        },
    )
    assert duplicate_reorder.status_code == 400

    duplicate_lesson = client.post(
        f"/v1/admin/courses/{course_id}/modules/module-a/lessons/lesson-b/duplicate"
    )
    assert duplicate_lesson.status_code == 200, duplicate_lesson.text

    duplicate_module = client.post(
        f"/v1/admin/courses/{course_id}/modules/module-a/duplicate"
    )
    assert duplicate_module.status_code == 200, duplicate_module.text

    archive_lesson = client.post(
        f"/v1/admin/courses/{course_id}/modules/module-a/lessons/lesson-a/archive"
    )
    assert archive_lesson.status_code == 200, archive_lesson.text

    archive_module = client.post(
        f"/v1/admin/courses/{course_id}/modules/module-b/archive"
    )
    assert archive_module.status_code == 200, archive_module.text

    module_publish = client.patch(
        f"/v1/admin/courses/{course_id}/modules/module-a",
        json={"status": "published"},
    )
    assert module_publish.status_code == 200, module_publish.text

    lesson_publish = client.patch(
        f"/v1/admin/courses/{course_id}/modules/module-a/lessons/lesson-b",
        json={"status": "published"},
    )
    assert lesson_publish.status_code == 200, lesson_publish.text

    authoring = client.get(f"/v1/admin/courses/{course_id}/authoring")
    assert authoring.status_code == 200, authoring.text
    payload = authoring.json()
    assert [module["module_id"] for module in payload["modules"]] == [
        "module-b",
        "module-a",
        payload["modules"][2]["module_id"],
    ]
    assert payload["modules"][0]["status"] == "archived"
    assert payload["modules"][2]["title"] == "module-a copy"
    assert payload["modules"][2]["status"] == "draft"
    lesson_ids = [lesson["lesson_id"] for lesson in payload["modules"][1]["lessons"]]
    assert lesson_ids[0] == "lesson-b"
    assert lesson_ids[2] == "lesson-a"
    assert payload["modules"][1]["lessons"][1]["title"] == "lesson-b copy"
    assert payload["modules"][1]["lessons"][1]["status"] == "draft"
    assert payload["modules"][1]["lessons"][2]["status"] == "archived"
    assert payload["readiness"]["ready_to_publish"] is True

    publish_ok = client.post(f"/v1/admin/courses/{course_id}/publish")
    assert publish_ok.status_code == 200, publish_ok.text

    published_authoring = client.get(f"/v1/admin/courses/{course_id}/authoring")
    assert published_authoring.status_code == 200, published_authoring.text
    published_payload = published_authoring.json()
    assert published_payload["has_unpublished_changes"] is False
    assert published_payload["published_version"] == published_payload["version"]


def test_admin_courses_list_filters_by_status_teacher_and_search() -> None:
    client = _client_with_actor("admin-1", ["admin"])

    first = client.post(
        "/v1/admin/courses",
        json={
            "title": "Studio Draft",
            "teacher_id": "teacher-1",
            "starts_at": "2026-09-01T09:00:00Z",
            "duration_days": 30,
            "slug": "studio-draft",
        },
    )
    second = client.post(
        "/v1/admin/courses",
        json={
            "title": "Other Course",
            "teacher_id": "teacher-22",
            "starts_at": "2026-09-01T09:00:00Z",
            "duration_days": 30,
            "slug": "other-course",
        },
    )
    assert first.status_code == 201, first.text
    assert second.status_code == 201, second.text

    response = client.get(
        "/v1/admin/courses",
        params={
            "publish_state": "draft",
            "teacher_id": "teacher-1",
            "q": "studio",
            "limit": 50,
            "offset": 0,
        },
    )
    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["limit"] == 50
    assert payload["offset"] == 0
    assert payload["total"] == 1
    assert [item["course_id"] for item in payload["items"]] == [
        first.json()["course_id"]
    ]
    assert payload["items"][0]["publish_state"] == "draft"
    assert payload["items"][0]["created_by"] == "admin-1"
    assert payload["items"][0]["updated_by"] == "admin-1"


def test_teacher_courses_list_is_scoped_to_owner() -> None:
    os.environ["COURSE_USE_INMEMORY"] = "1"
    get_runtime.cache_clear()
    app = create_app()
    actor_state = {"actor_id": "admin-1", "roles": ["admin"]}
    app.dependency_overrides[get_http_actor] = lambda: HttpActor(
        actor_id=actor_state["actor_id"],
        roles=actor_state["roles"],
    )
    client = TestClient(app)

    first = client.post(
        "/v1/admin/courses",
        json={
            "title": "Teacher Owned",
            "teacher_id": "teacher-1",
            "starts_at": "2026-09-01T09:00:00Z",
            "duration_days": 30,
        },
    )
    second = client.post(
        "/v1/admin/courses",
        json={
            "title": "Other Teacher Owned",
            "teacher_id": "teacher-22",
            "starts_at": "2026-09-01T09:00:00Z",
            "duration_days": 30,
        },
    )
    assert first.status_code == 201, first.text
    assert second.status_code == 201, second.text

    actor_state["actor_id"] = "teacher-1"
    actor_state["roles"] = ["teacher"]
    response = client.get("/v1/admin/courses")
    assert response.status_code == 200, response.text
    assert response.json()["total"] == 1
    assert [item["course_id"] for item in response.json()["items"]] == [
        first.json()["course_id"]
    ]

    denied = client.get("/v1/admin/courses", params={"teacher_id": "teacher-22"})
    assert denied.status_code == 403


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
