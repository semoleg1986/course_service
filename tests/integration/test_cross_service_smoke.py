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


def test_auth_token_accepted_by_course_service(auth_service_base_url: str) -> None:
    status, login = _http_json(
        "POST",
        f"{auth_service_base_url}/v1/auth/login",
        payload={
            "email": "admin@example.com",
            "password": "admin12345",
            "session_fingerprint": "course-cross-smoke",
        },
    )
    assert status == 200
    access_token = login["access_token"]

    os.environ["COURSE_AUTH_JWKS_URL"] = f"{auth_service_base_url}/.well-known/jwks.json"
    os.environ["COURSE_AUTH_ISSUER"] = "auth_service"
    os.environ.pop("COURSE_AUTH_JWKS_JSON", None)
    get_runtime.cache_clear()

    client = TestClient(create_app())
    response = client.post(
        "/internal/v1/access/check-by-token",
        json={
            "course_id": "00000000-0000-0000-0000-000000000001",
            "student_id": "student-1",
            "require_active_grant": True,
            "require_enrollment": True,
        },
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["decision"] == "allow"
    assert body["reason_code"] == "admin_override"
