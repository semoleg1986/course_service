from __future__ import annotations

from fastapi.testclient import TestClient

from src.interface.http.app import create_app
from src.interface.http.observability import reset_metrics


def test_healthz() -> None:
    reset_metrics()
    client = TestClient(create_app())
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    assert response.headers.get("X-Content-Type-Options") == "nosniff"
    assert response.headers.get("X-Frame-Options") == "DENY"
    assert response.headers.get("Referrer-Policy") == "no-referrer"
    assert (
        response.headers.get("Permissions-Policy")
        == "camera=(), microphone=(), geolocation=()"
    )


def test_metrics_endpoint_exposes_prometheus_metrics() -> None:
    reset_metrics()
    client = TestClient(create_app())
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "http_requests_total" in response.text
    assert "http_request_duration_seconds" in response.text
    assert "http_errors_total" in response.text
