from __future__ import annotations

import json
import os
import socket
import subprocess
import time
from pathlib import Path
from urllib.request import Request, urlopen

import pytest
from fastapi.testclient import TestClient

from src.interface.http.app import create_app
from src.interface.http.wiring import get_runtime

pytestmark = pytest.mark.integration
_AUDIENCE = "platform_clients"
_SERVICE_TOKEN = "cross-service-token"


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _http_json(
    method: str,
    url: str,
    payload: dict | None = None,
    headers: dict[str, str] | None = None,
) -> tuple[int, dict]:
    raw = json.dumps(payload).encode("utf-8") if payload is not None else None
    request = Request(url=url, data=raw, method=method)
    request.add_header("Content-Type", "application/json")
    for key, value in (headers or {}).items():
        request.add_header(key, value)
    with urlopen(request, timeout=5) as response:
        body = response.read().decode("utf-8")
        return int(response.status), (json.loads(body) if body else {})


@pytest.fixture(scope="session")
def auth_service_base_url() -> str:
    auth_root = Path("/Users/olegsemenov/Programming/curs/auth_service")
    port = _free_port()
    base_url = f"http://127.0.0.1:{port}"

    env = os.environ.copy()
    env["AUTH_USE_INMEMORY"] = "1"
    env["AUTH_AUTO_CREATE_SCHEMA"] = "0"
    env["AUTH_JWT_AUDIENCE"] = _AUDIENCE
    env.pop("AUTH_DATABASE_URL", None)

    process = subprocess.Popen(
        [
            "python",
            "-m",
            "uvicorn",
            "src.interface.http.main:app",
            "--host",
            "127.0.0.1",
            "--port",
            str(port),
            "--log-level",
            "warning",
        ],
        cwd=str(auth_root),
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    deadline = time.time() + 12
    while time.time() < deadline:
        if process.poll() is not None:
            raise RuntimeError("auth_service не запустился для smoke теста.")
        try:
            status, _ = _http_json("GET", f"{base_url}/healthz")
            if status == 200:
                break
        except Exception:
            time.sleep(0.15)
    else:
        process.terminate()
        process.wait(timeout=5)
        raise RuntimeError("auth_service healthcheck timeout.")

    try:
        yield base_url
    finally:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)


@pytest.fixture(scope="session")
def users_service_base_url(auth_service_base_url: str) -> str:
    users_root = Path("/Users/olegsemenov/Programming/curs/users_service")
    port = _free_port()
    base_url = f"http://127.0.0.1:{port}"

    env = os.environ.copy()
    env["USERS_USE_INMEMORY"] = "1"
    env["USERS_AUTO_CREATE_SCHEMA"] = "0"
    env["USERS_AUTH_ISSUER"] = "auth_service"
    env["USERS_AUTH_AUDIENCE"] = _AUDIENCE
    env["USERS_AUTH_JWKS_URL"] = f"{auth_service_base_url}/.well-known/jwks.json"
    env["USERS_SERVICE_TOKEN"] = _SERVICE_TOKEN
    env.pop("USERS_DATABASE_URL", None)

    process = subprocess.Popen(
        [
            "python",
            "-m",
            "uvicorn",
            "src.interface.http.main:app",
            "--host",
            "127.0.0.1",
            "--port",
            str(port),
            "--log-level",
            "warning",
        ],
        cwd=str(users_root),
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    deadline = time.time() + 12
    while time.time() < deadline:
        if process.poll() is not None:
            raise RuntimeError("users_service не запустился для smoke теста.")
        try:
            status, _ = _http_json("GET", f"{base_url}/healthz")
            if status == 200:
                break
        except Exception:
            time.sleep(0.15)
    else:
        process.terminate()
        process.wait(timeout=5)
        raise RuntimeError("users_service healthcheck timeout.")

    try:
        yield base_url
    finally:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)


def test_create_course_uses_users_teacher_directory(
    auth_service_base_url: str,
    users_service_base_url: str,
) -> None:
    status, login = _http_json(
        "POST",
        f"{auth_service_base_url}/v1/auth/login",
        payload={
            "email": "admin@example.com",
            "password": "admin12345",
            "session_fingerprint": "course-teacher-cross-smoke",
        },
    )
    assert status == 200
    access_token = login["access_token"]

    status, created = _http_json(
        "POST",
        f"{users_service_base_url}/v1/admin/users",
        payload={
            "user_id": "teacher-cross-1",
            "email": "teacher-cross-1@example.com",
            "display_name": "Teacher Cross 1",
            "phone": None,
            "roles": ["teacher"],
        },
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert status == 201, created

    os.environ["COURSE_USE_INMEMORY"] = "1"
    os.environ["COURSE_AUTO_CREATE_SCHEMA"] = "0"
    os.environ["COURSE_AUTH_JWKS_URL"] = (
        f"{auth_service_base_url}/.well-known/jwks.json"
    )
    os.environ["COURSE_AUTH_ISSUER"] = "auth_service"
    os.environ["COURSE_AUTH_AUDIENCE"] = _AUDIENCE
    os.environ["COURSE_USERS_SERVICE_BASE_URL"] = users_service_base_url
    os.environ["COURSE_USERS_SERVICE_TOKEN"] = _SERVICE_TOKEN
    os.environ.pop("COURSE_DATABASE_URL", None)
    get_runtime.cache_clear()

    client = TestClient(create_app())
    response = client.post(
        "/v1/admin/courses",
        json={
            "title": "Cross service course",
            "teacher_id": "teacher-cross-1",
            "starts_at": "2026-09-01T09:00:00Z",
            "duration_days": 30,
        },
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["teacher_id"] == "teacher-cross-1"
    assert body["teacher_display_name"] == "Teacher Cross 1"


def test_create_course_requires_bearer_token_in_cross_service_mode(
    auth_service_base_url: str,
    users_service_base_url: str,
) -> None:
    del auth_service_base_url, users_service_base_url
    client = TestClient(create_app())
    response = client.post(
        "/v1/admin/courses",
        json={
            "title": "No token course",
            "teacher_id": "teacher-any",
            "starts_at": "2026-09-01T09:00:00Z",
            "duration_days": 30,
        },
    )
    assert response.status_code == 401


def test_teacher_cannot_create_course_for_another_teacher_cross_service(
    auth_service_base_url: str,
    users_service_base_url: str,
) -> None:
    status, _ = _http_json(
        "POST",
        f"{auth_service_base_url}/v1/auth/register",
        payload={
            "email": "teacher-cross-owner@example.com",
            "password": "teacher12345",
            "default_role": "teacher",
        },
    )
    assert status == 201

    status, login_teacher = _http_json(
        "POST",
        f"{auth_service_base_url}/v1/auth/login",
        payload={
            "email": "teacher-cross-owner@example.com",
            "password": "teacher12345",
            "session_fingerprint": "teacher-cross-owner",
        },
    )
    assert status == 200
    teacher_access_token = login_teacher["access_token"]

    status, _ = _http_json(
        "POST",
        f"{users_service_base_url}/v1/admin/users",
        payload={
            "user_id": "teacher-cross-owner",
            "email": "teacher-cross-owner@example.com",
            "display_name": "Teacher Cross Owner",
            "phone": None,
            "roles": ["teacher"],
        },
        headers={"Authorization": f"Bearer {teacher_access_token}"},
    )
    assert status == 201

    status, login_admin = _http_json(
        "POST",
        f"{auth_service_base_url}/v1/auth/login",
        payload={
            "email": "admin@example.com",
            "password": "admin12345",
            "session_fingerprint": "admin-cross-owner",
        },
    )
    assert status == 200
    admin_access_token = login_admin["access_token"]
    status, _ = _http_json(
        "POST",
        f"{users_service_base_url}/v1/admin/users",
        payload={
            "user_id": "teacher-cross-other",
            "email": "teacher-cross-other@example.com",
            "display_name": "Teacher Cross Other",
            "phone": None,
            "roles": ["teacher"],
        },
        headers={"Authorization": f"Bearer {admin_access_token}"},
    )
    assert status == 201

    os.environ["COURSE_USE_INMEMORY"] = "1"
    os.environ["COURSE_AUTO_CREATE_SCHEMA"] = "0"
    os.environ["COURSE_AUTH_JWKS_URL"] = (
        f"{auth_service_base_url}/.well-known/jwks.json"
    )
    os.environ["COURSE_AUTH_ISSUER"] = "auth_service"
    os.environ["COURSE_AUTH_AUDIENCE"] = _AUDIENCE
    os.environ["COURSE_USERS_SERVICE_BASE_URL"] = users_service_base_url
    os.environ["COURSE_USERS_SERVICE_TOKEN"] = _SERVICE_TOKEN
    os.environ.pop("COURSE_DATABASE_URL", None)
    get_runtime.cache_clear()

    client = TestClient(create_app())
    response = client.post(
        "/v1/admin/courses",
        json={
            "title": "Forbidden owner mismatch",
            "teacher_id": "teacher-cross-other",
            "starts_at": "2026-09-01T09:00:00Z",
            "duration_days": 30,
        },
        headers={"Authorization": f"Bearer {teacher_access_token}"},
    )
    assert response.status_code == 403


def test_create_course_returns_409_for_unknown_teacher_cross_service(
    auth_service_base_url: str,
    users_service_base_url: str,
) -> None:
    status, login = _http_json(
        "POST",
        f"{auth_service_base_url}/v1/auth/login",
        payload={
            "email": "admin@example.com",
            "password": "admin12345",
            "session_fingerprint": "unknown-teacher-cross",
        },
    )
    assert status == 200
    access_token = login["access_token"]

    os.environ["COURSE_USE_INMEMORY"] = "1"
    os.environ["COURSE_AUTO_CREATE_SCHEMA"] = "0"
    os.environ["COURSE_AUTH_JWKS_URL"] = (
        f"{auth_service_base_url}/.well-known/jwks.json"
    )
    os.environ["COURSE_AUTH_ISSUER"] = "auth_service"
    os.environ["COURSE_AUTH_AUDIENCE"] = _AUDIENCE
    os.environ["COURSE_USERS_SERVICE_BASE_URL"] = users_service_base_url
    os.environ["COURSE_USERS_SERVICE_TOKEN"] = _SERVICE_TOKEN
    os.environ.pop("COURSE_DATABASE_URL", None)
    get_runtime.cache_clear()

    client = TestClient(create_app())
    response = client.post(
        "/v1/admin/courses",
        json={
            "title": "Unknown teacher",
            "teacher_id": "teacher-missing-404",
            "starts_at": "2026-09-01T09:00:00Z",
            "duration_days": 30,
        },
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == 409
    assert "teacher_id не найден" in response.json()["detail"]
