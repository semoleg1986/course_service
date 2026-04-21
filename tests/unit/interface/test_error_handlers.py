from __future__ import annotations

from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

from src.interface.http.errors import register_exception_handlers
from src.interface.http.observability import install_observability


def test_http_error_response_contains_request_id() -> None:
    app = FastAPI()
    install_observability(app)
    register_exception_handlers(app)

    @app.get("/denied")
    def denied() -> None:
        raise HTTPException(status_code=403, detail="forbidden")

    client = TestClient(app)
    response = client.get("/denied", headers={"X-Request-ID": "req-course-001"})

    assert response.status_code == 403
    assert response.headers.get("X-Request-ID") == "req-course-001"
    assert response.json().get("request_id") == "req-course-001"
    assert response.json().get("detail") == "forbidden"
