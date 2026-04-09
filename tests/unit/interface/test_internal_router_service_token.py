from __future__ import annotations

import os

from fastapi.testclient import TestClient

from src.interface.http.app import create_app
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
