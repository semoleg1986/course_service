"""Настройки запуска course_service."""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Settings:
    """Параметры runtime-конфигурации."""

    service_token: str
    database_url: str
    use_inmemory: bool
    auto_create_schema: bool
    auth_jwks_url: str
    auth_jwks_json: str | None
    auth_issuer: str
    auth_audience: str
    users_service_base_url: str
    users_service_token: str
    users_service_timeout_seconds: float

    @classmethod
    def from_env(cls) -> "Settings":
        """Читает конфигурацию из переменных окружения."""

        return cls(
            service_token=os.getenv("COURSE_SERVICE_TOKEN", "dev-service-token"),
            database_url=os.getenv(
                "COURSE_DATABASE_URL", "sqlite:///./course_service.db"
            ),
            use_inmemory=os.getenv("COURSE_USE_INMEMORY", "1") == "1",
            auto_create_schema=os.getenv("COURSE_AUTO_CREATE_SCHEMA", "0") == "1",
            auth_jwks_url=os.getenv(
                "COURSE_AUTH_JWKS_URL",
                "http://localhost:8000/.well-known/jwks.json",
            ),
            auth_jwks_json=os.getenv("COURSE_AUTH_JWKS_JSON"),
            auth_issuer=os.getenv("COURSE_AUTH_ISSUER", "auth_service"),
            auth_audience=os.getenv("COURSE_AUTH_AUDIENCE", "platform_clients"),
            users_service_base_url=os.getenv(
                "COURSE_USERS_SERVICE_BASE_URL", "http://localhost:8002"
            ),
            users_service_token=os.getenv(
                "COURSE_USERS_SERVICE_TOKEN", "dev-service-token"
            ),
            users_service_timeout_seconds=float(
                os.getenv("COURSE_USERS_SERVICE_TIMEOUT_SECONDS", "2")
            ),
        )
