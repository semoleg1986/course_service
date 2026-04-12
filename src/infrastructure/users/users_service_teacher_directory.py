"""HTTP адаптер каталога преподавателей users_service."""

from __future__ import annotations

import json
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

from src.application.ports.teacher_directory import TeacherInfo
from src.domain.errors import InvariantViolationError


class UsersServiceTeacherDirectory:
    """Реализация TeacherDirectory через internal API users_service."""

    def __init__(
        self, *, base_url: str, service_token: str, timeout_seconds: float = 2.0
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._service_token = service_token
        self._timeout_seconds = timeout_seconds

    def get_teacher(self, teacher_id: str) -> TeacherInfo | None:
        """Возвращает профиль преподавателя из users_service."""

        url = f"{self._base_url}/internal/v1/teachers/{quote(teacher_id)}"
        request = Request(
            url,
            headers={"X-Service-Token": self._service_token},
            method="GET",
        )
        try:
            with urlopen(request, timeout=self._timeout_seconds) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            if exc.code in (401, 404):
                return None
            raise InvariantViolationError(
                "Не удалось проверить преподавателя в users_service."
            ) from exc
        except (TimeoutError, URLError, json.JSONDecodeError) as exc:
            raise InvariantViolationError(
                "Не удалось проверить преподавателя в users_service."
            ) from exc

        roles_raw = payload.get("roles", [])
        roles = [str(item).strip() for item in roles_raw if str(item).strip()]
        teacher_result_id = str(payload.get("teacher_id", "")).strip()
        display_name = str(payload.get("display_name", "")).strip()
        status = str(payload.get("status", "")).strip()
        if not teacher_result_id or not display_name:
            raise InvariantViolationError(
                "users_service вернул некорректный профиль преподавателя."
            )
        return TeacherInfo(
            teacher_id=teacher_result_id,
            display_name=display_name,
            status=status,
            roles=roles,
        )
