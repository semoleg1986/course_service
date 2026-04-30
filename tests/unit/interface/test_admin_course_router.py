from __future__ import annotations

import os

from fastapi.testclient import TestClient

from src.interface.http.app import create_app
from src.interface.http.common.actor import HttpActor
from src.interface.http.v1.admin.router import get_http_actor
from src.interface.http.wiring import get_runtime


def _client_with_actor(actor_id: str, roles: list[str]) -> TestClient:
    os.environ["COURSE_USE_INMEMORY"] = "1"
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
