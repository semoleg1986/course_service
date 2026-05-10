"""HTTP adapter for parent lookup via users_service."""

from __future__ import annotations

import json
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

from src.domain.errors import InvariantViolationError
from src.interface.http.observability import current_correlation_id


class UsersServiceStudentParentDirectory:
    """Resolves active parents for a student via internal users_service API."""

    def __init__(
        self, *, base_url: str, service_token: str, timeout_seconds: float = 2.0
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._service_token = service_token
        self._timeout_seconds = timeout_seconds

    def list_parent_ids(self, student_id: str) -> list[str]:
        url = f"{self._base_url}/internal/v1/students/{quote(student_id)}/parents"
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
        except HTTPError as exc:
            if exc.code in (401, 404):
                return []
            raise InvariantViolationError(
                "Не удалось получить parent ids из users_service."
            ) from exc
        except (TimeoutError, URLError, json.JSONDecodeError) as exc:
            raise InvariantViolationError(
                "Не удалось получить parent ids из users_service."
            ) from exc

        parent_ids_raw = payload.get("parent_ids", [])
        return sorted(
            {str(item).strip() for item in parent_ids_raw if str(item).strip()}
        )
