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
from src.interface.http.wiring import get_runtime


def _client_with_actor(actor_id: str, roles: list[str]) -> TestClient:
    os.environ["COURSE_USE_INMEMORY"] = "1"
    get_runtime.cache_clear()
    app = create_app()
    app.dependency_overrides[get_http_actor] = lambda: HttpActor(
        actor_id=actor_id,
        roles=roles,
    )
    return TestClient(app)


def _prepare_course_with_published_lessons(course_slug: str) -> str:
    runtime = get_runtime()
    facade = runtime.facade
    now = datetime(2026, 5, 2, 12, 0, tzinfo=UTC)

    created = facade.execute(
        CreateCourseCommand(
            title=f"Course {course_slug}",
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
            slug=course_slug,
            seo_meta_title=f"SEO {course_slug}",
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
    for lesson_id in ["lesson-1", "lesson-2"]:
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
        "student-1",
        "approved",
    )
    return created.course_id


def test_student_complete_lesson_happy_path_and_idempotency() -> None:
    client = _client_with_actor("student-1", ["student"])
    course_id = _prepare_course_with_published_lessons("student-course-1")

    response = client.post(f"/v1/student/courses/{course_id}/lessons/lesson-1/complete")
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["lesson_status"] == "completed"
    assert body["course_status"] == "in_progress"
    assert body["completed_lessons"] == 1
    assert body["total_lessons"] == 2
    assert body["progress_percent"] == 50.0

    repeated = client.post(f"/v1/student/courses/{course_id}/lessons/lesson-1/complete")
    assert repeated.status_code == 200, repeated.text
    assert repeated.json()["completed_lessons"] == 1

    progress = client.get(f"/v1/student/courses/{course_id}/progress")
    assert progress.status_code == 200, progress.text
    progress_body = progress.json()
    assert progress_body["course_id"] == course_id
    assert progress_body["status"] == "in_progress"
    assert progress_body["progress_percent"] == 50.0
    assert progress_body["completed_lessons"] == 1
    assert progress_body["total_lessons"] == 2


def test_student_complete_lesson_requires_active_access() -> None:
    client = _client_with_actor("student-2", ["student"])
    course_id = _prepare_course_with_published_lessons("student-course-2")

    response = client.post(f"/v1/student/courses/{course_id}/lessons/lesson-1/complete")
    assert response.status_code == 403, response.text


def test_student_complete_lesson_rejects_non_student() -> None:
    client = _client_with_actor("parent-1", ["parent"])
    course_id = _prepare_course_with_published_lessons("student-course-3")

    response = client.post(f"/v1/student/courses/{course_id}/lessons/lesson-1/complete")
    assert response.status_code == 403, response.text


def test_student_complete_lesson_returns_404_for_unknown_lesson() -> None:
    client = _client_with_actor("student-1", ["student"])
    course_id = _prepare_course_with_published_lessons("student-course-4")

    response = client.post(f"/v1/student/courses/{course_id}/lessons/missing/complete")
    assert response.status_code == 404, response.text


def test_student_get_progress_returns_not_started_when_empty() -> None:
    client = _client_with_actor("student-1", ["student"])
    course_id = _prepare_course_with_published_lessons("student-course-5")

    response = client.get(f"/v1/student/courses/{course_id}/progress")
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["status"] == "not_started"
    assert body["progress_percent"] == 0.0
    assert body["completed_lessons"] == 0
    assert body["total_lessons"] == 2


def test_student_get_progress_requires_active_access() -> None:
    client = _client_with_actor("student-2", ["student"])
    course_id = _prepare_course_with_published_lessons("student-course-6")

    response = client.get(f"/v1/student/courses/{course_id}/progress")
    assert response.status_code == 403, response.text
