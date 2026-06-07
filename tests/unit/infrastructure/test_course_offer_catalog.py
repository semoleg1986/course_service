from __future__ import annotations

from io import BytesIO

from src.infrastructure.catalog.http_course_offer_catalog import HttpCourseOfferCatalog


class _Response:
    def __init__(self, body: bytes) -> None:
        self._body = BytesIO(body)

    def __enter__(self) -> "_Response":
        return self

    def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
        return None

    def read(self) -> bytes:
        return self._body.read()


def test_http_course_offer_catalog_reads_default_offer_status(monkeypatch) -> None:
    captured = {}

    def fake_urlopen(request, timeout):  # noqa: ANN001, ANN202
        captured["url"] = request.full_url
        captured["timeout"] = timeout
        captured["token"] = request.headers["X-service-token"]
        return _Response(b'{"has_active_default_offer": true}')

    monkeypatch.setattr(
        "src.infrastructure.catalog.http_course_offer_catalog.urlopen",
        fake_urlopen,
    )

    catalog = HttpCourseOfferCatalog(
        base_url="http://catalog:8007",
        service_token="service-token",
        timeout_seconds=3,
    )

    assert catalog.has_active_default_offer("course/1") is True
    assert captured["url"].endswith(
        "/internal/v1/courses/course%2F1/default-offer-status"
    )
    assert captured["timeout"] == 3
    assert captured["token"] == "service-token"


def test_http_course_offer_catalog_treats_invalid_response_as_not_ready(
    monkeypatch,
) -> None:
    def fake_urlopen(request, timeout):  # noqa: ANN001, ANN202
        return _Response(b"not json")

    monkeypatch.setattr(
        "src.infrastructure.catalog.http_course_offer_catalog.urlopen",
        fake_urlopen,
    )

    catalog = HttpCourseOfferCatalog(
        base_url="http://catalog:8007",
        service_token="service-token",
    )

    assert catalog.has_active_default_offer("course-1") is False
