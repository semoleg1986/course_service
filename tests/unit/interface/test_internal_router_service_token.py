from __future__ import annotations

import os

from fastapi.testclient import TestClient

from src.interface.http.app import create_app
from src.interface.http.common.actor import HttpActor
from src.interface.http.v1.admin.router import get_http_actor as get_admin_http_actor
from src.interface.http.wiring import get_runtime


def _client() -> TestClient:
    os.environ["COURSE_USE_INMEMORY"] = "1"
    os.environ["COURSE_SERVICE_TOKEN"] = "svc-token"
    get_runtime.cache_clear()
    return TestClient(create_app())


def test_internal_check_requires_service_token() -> None:
    client = _client()

    missing = client.post(
        "/internal/v1/access/check",
        json={
            "course_id": "course-1",
            "actor_account_id": "u-1",
            "actor_roles": ["student"],
        },
    )
    assert missing.status_code == 401

    wrong = client.post(
        "/internal/v1/access/check",
        json={
            "course_id": "course-1",
            "actor_account_id": "u-1",
            "actor_roles": ["student"],
        },
        headers={"X-Service-Token": "wrong"},
    )
    assert wrong.status_code == 401

    ok = client.post(
        "/internal/v1/access/check",
        json={
            "course_id": "course-1",
            "actor_account_id": "u-1",
            "actor_roles": ["student"],
        },
        headers={"X-Service-Token": "svc-token"},
    )
    assert ok.status_code == 200


def test_internal_course_payment_snapshot_contract() -> None:
    client = _client()
    app = client.app
    app.dependency_overrides[get_admin_http_actor] = lambda: HttpActor(
        actor_id="admin-1", roles=["admin"]
    )

    create = client.post(
        "/v1/admin/courses",
        json={
            "title": "Snapshot Course",
            "teacher_id": "teacher-1",
            "starts_at": "2026-09-01T09:00:00Z",
            "duration_days": 30,
            "access_ttl_days": 45,
            "price": 150,
            "currency": "USD",
        },
    )
    assert create.status_code == 201, create.text
    course_id = create.json()["course_id"]

    response = client.get(
        f"/internal/v1/access/courses/{course_id}/payment-snapshot",
        headers={"X-Service-Token": "svc-token"},
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["course_id"] == course_id
    assert body["price"] == 150
    assert body["currency"] == "USD"
    assert body["access_ttl_days"] == 45
