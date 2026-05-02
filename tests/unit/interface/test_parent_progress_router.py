from __future__ import annotations

import os
from datetime import UTC, datetime

from fastapi.testclient import TestClient

from src.application.courses.commands.dto import (
    AddLessonCommand,
    AddModuleCommand,
    CreateCourseCommand,
    PublishCourseCommand,
    UpdateLessonCommand,
    UpdateModuleCommand,
)
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


def _prepare_parent_progress_course(
    *,
    slug: str,
    student_id: str,
    lesson_count: int = 2,
    completed_lessons: int = 0,
) -> tuple[str, datetime | None]:
    runtime = get_runtime()
    facade = runtime.facade
    now = datetime(2026, 5, 2, 12, 0, tzinfo=UTC)

    created = facade.execute(
        CreateCourseCommand(
            title=f"Course {slug}",
            description="desc",
            teacher_id="teacher-1",
            teacher_display_name="Teacher 1",
            starts_at=now,
            duration_days=30,
            access_ttl_days=None,
            enrollment_opens_at=None,
            enrollment_closes_at=None,
            price=0.0,
            currency="USD",
            language="ru",
            age_min=None,
            age_max=None,
            level="beginner",
            tags=[],
            cover_image_url=None,
            is_live_enabled=False,
            live_room_template_id=None,
            timezone="UTC",
            max_students=None,
            slug=slug,
            seo_meta_title=f"SEO {slug}",
            seo_meta_description="desc",
            seo_canonical_url=None,
            seo_robots="index",
            seo_og_image_url=None,
            actor_id="teacher-1",
            actor_roles=["teacher"],
        )
    )
    facade.execute(
        AddModuleCommand(
            course_id=created.course_id,
            module_id="module-1",
            title="Module 1",
            description=None,
            is_required=True,
            released_at=None,
            actor_id="teacher-1",
            actor_roles=["teacher"],
        )
    )
    for index in range(lesson_count):
        lesson_id = f"lesson-{index + 1}"
        facade.execute(
            AddLessonCommand(
                course_id=created.course_id,
                module_id="module-1",
                lesson_id=lesson_id,
                title=lesson_id,
                description=None,
                content_type="video",
                content_ref=None,
                duration_minutes=10,
                is_preview=False,
                released_at=None,
                actor_id="teacher-1",
                actor_roles=["teacher"],
            )
        )
        facade.execute(
            UpdateLessonCommand(
                course_id=created.course_id,
                module_id="module-1",
                lesson_id=lesson_id,
                actor_id="teacher-1",
                actor_roles=["teacher"],
                status="published",
            )
        )
    facade.execute(
        UpdateModuleCommand(
            course_id=created.course_id,
            module_id="module-1",
            actor_id="teacher-1",
            actor_roles=["teacher"],
            status="published",
        )
    )
    facade.execute(
        PublishCourseCommand(
            course_id=created.course_id,
            actor_id="teacher-1",
            actor_roles=["teacher"],
        )
    )
    runtime.access_read_model.seed_course_owner(created.course_id, "teacher-1")
    runtime.access_read_model.seed_access_grant_status(
        created.course_id,
        student_id,
        "approved",
    )
    runtime.access_read_model.seed_enrollment_status(
        created.course_id,
        student_id,
        "active",
    )

    completed_at = None
    if completed_lessons:
        completed_at = now.replace(hour=13)
        for index in range(completed_lessons):
            lesson_id = f"lesson-{index + 1}"
            runtime.access_read_model.upsert_lesson_progress(
                course_id=created.course_id,
                module_id="module-1",
                lesson_id=lesson_id,
                student_id=student_id,
                progress_id=f"progress-{slug}-{lesson_id}",
                status="completed",
                created_at=now,
                created_by=student_id,
                updated_at=completed_at,
                updated_by=student_id,
                version=2,
                started_at=now,
                completed_at=completed_at,
                last_activity_at=completed_at,
            )
    return created.course_id, completed_at


def test_parent_progress_happy_path_with_pagination_and_filter() -> None:
    client = _client_with_actor("parent-1", ["parent"])
    course_id_1, _ = _prepare_parent_progress_course(
        slug="parent-progress-1",
        student_id="student-1",
        completed_lessons=1,
    )
    course_id_2, _ = _prepare_parent_progress_course(
        slug="parent-progress-2",
        student_id="student-1",
        completed_lessons=2,
    )

    response = client.get(
        "/v1/parent/students/student-1/courses/progress?limit=20&offset=0&status=in_progress"
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["limit"] == 20
    assert body["offset"] == 0
    assert body["status"] == "in_progress"
    assert len(body["items"]) == 1
    assert body["items"][0]["course_id"] == course_id_1
    assert body["items"][0]["progress_percent"] == 50.0
    assert body["items"][0]["completed_lessons"] == 1
    assert body["items"][0]["total_lessons"] == 2
    assert body["items"][0]["status"] == "in_progress"

    completed_only = client.get(
        "/v1/parent/students/student-1/courses/progress?limit=1&offset=0&status=completed"
    )
    assert completed_only.status_code == 200, completed_only.text
    completed_items = completed_only.json()["items"]
    assert len(completed_items) == 1
    assert completed_items[0]["course_id"] == course_id_2
    assert completed_items[0]["status"] == "completed"
    assert completed_items[0]["progress_percent"] == 100.0

    metrics = client.get("/metrics")
    assert metrics.status_code == 200
    assert (
        'parent_progress_requests_total{result="success",status_filter="in_progress"} 1'
        in metrics.text
    )
    assert (
        'parent_progress_requests_total{result="success",status_filter="completed"} 1'
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
    course_id, completed_at = _prepare_parent_progress_course(
        slug="parent-completed-1",
        student_id="student-1",
        completed_lessons=2,
    )
    assert completed_at is not None

    response = client.get(
        "/v1/parent/students/student-1/courses/completed?limit=10&offset=0&viewer_timezone=Asia/Tbilisi"
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["limit"] == 10
    assert body["offset"] == 0
    assert body["viewer_timezone"] == "Asia/Tbilisi"
    assert isinstance(body["items"], list)
    assert len(body["items"]) == 1
    assert body["items"][0]["course_id"] == course_id
    assert body["items"][0]["completed_at"] == completed_at.isoformat().replace(
        "+00:00", "Z"
    )
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
