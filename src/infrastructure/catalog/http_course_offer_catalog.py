"""HTTP CourseOfferCatalog adapter for commercial_catalog_service."""

from __future__ import annotations

import json
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

from src.interface.http.observability import current_correlation_id


class HttpCourseOfferCatalog:
    """Reads course offer readiness from commercial_catalog_service."""

    def __init__(
        self, *, base_url: str, service_token: str, timeout_seconds: float = 2.0
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._service_token = service_token
        self._timeout_seconds = timeout_seconds

    def has_active_default_offer(self, course_id: str) -> bool:
        url = (
            f"{self._base_url}/internal/v1/courses/{quote(course_id, safe='')}"
            "/default-offer-status"
        )
        request = Request(
            url,
            headers={
                "X-Service-Token": self._service_token,
                **(
                    {"X-Correlation-ID": current_correlation_id()}
                    if current_correlation_id() is not None
                    else {}
                ),
            },
            method="GET",
        )
        try:
            with urlopen(request, timeout=self._timeout_seconds) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except (HTTPError, TimeoutError, URLError, json.JSONDecodeError):
            return False

        return bool(payload.get("has_active_default_offer"))
