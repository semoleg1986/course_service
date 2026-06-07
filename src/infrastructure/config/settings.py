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
    bonus_enabled: bool
    bonus_course_completion_points: int
    bonus_service_base_url: str
    bonus_service_token: str
    bonus_service_timeout_seconds: float
    commercial_catalog_service_base_url: str
    commercial_catalog_service_token: str
    commercial_catalog_service_timeout_seconds: float
    student_complete_rate_limit_max: int
    student_complete_rate_limit_window_seconds: int
    student_progress_rate_limit_max: int
    student_progress_rate_limit_window_seconds: int
    parent_progress_rate_limit_max: int
    parent_progress_rate_limit_window_seconds: int
    parent_completed_rate_limit_max: int
    parent_completed_rate_limit_window_seconds: int
    admin_publish_rate_limit_max: int
    admin_publish_rate_limit_window_seconds: int
    admin_archive_rate_limit_max: int
    admin_archive_rate_limit_window_seconds: int

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
            bonus_enabled=os.getenv("COURSE_BONUS_ENABLED", "0") == "1",
            bonus_course_completion_points=int(
                os.getenv("COURSE_BONUS_COURSE_COMPLETION_POINTS", "25")
            ),
            bonus_service_base_url=os.getenv(
                "COURSE_BONUS_SERVICE_BASE_URL", "http://localhost:8006"
            ),
            bonus_service_token=os.getenv(
                "COURSE_BONUS_SERVICE_TOKEN", "dev-service-token"
            ),
            bonus_service_timeout_seconds=float(
                os.getenv("COURSE_BONUS_SERVICE_TIMEOUT_SECONDS", "2")
            ),
            commercial_catalog_service_base_url=os.getenv(
                "COURSE_COMMERCIAL_CATALOG_SERVICE_BASE_URL",
                "http://localhost:8007",
            ),
            commercial_catalog_service_token=os.getenv(
                "COURSE_COMMERCIAL_CATALOG_SERVICE_TOKEN",
                "dev-service-token",
            ),
            commercial_catalog_service_timeout_seconds=float(
                os.getenv("COURSE_COMMERCIAL_CATALOG_SERVICE_TIMEOUT_SECONDS", "2")
            ),
            student_complete_rate_limit_max=int(
                os.getenv("COURSE_RATE_LIMIT_STUDENT_COMPLETE_MAX", "20")
            ),
            student_complete_rate_limit_window_seconds=int(
                os.getenv("COURSE_RATE_LIMIT_STUDENT_COMPLETE_WINDOW_SECONDS", "60")
            ),
            student_progress_rate_limit_max=int(
                os.getenv("COURSE_RATE_LIMIT_STUDENT_PROGRESS_MAX", "60")
            ),
            student_progress_rate_limit_window_seconds=int(
                os.getenv("COURSE_RATE_LIMIT_STUDENT_PROGRESS_WINDOW_SECONDS", "60")
            ),
            parent_progress_rate_limit_max=int(
                os.getenv("COURSE_RATE_LIMIT_PARENT_PROGRESS_MAX", "60")
            ),
            parent_progress_rate_limit_window_seconds=int(
                os.getenv("COURSE_RATE_LIMIT_PARENT_PROGRESS_WINDOW_SECONDS", "60")
            ),
            parent_completed_rate_limit_max=int(
                os.getenv("COURSE_RATE_LIMIT_PARENT_COMPLETED_MAX", "60")
            ),
            parent_completed_rate_limit_window_seconds=int(
                os.getenv("COURSE_RATE_LIMIT_PARENT_COMPLETED_WINDOW_SECONDS", "60")
            ),
            admin_publish_rate_limit_max=int(
                os.getenv("COURSE_RATE_LIMIT_ADMIN_PUBLISH_MAX", "20")
            ),
            admin_publish_rate_limit_window_seconds=int(
                os.getenv("COURSE_RATE_LIMIT_ADMIN_PUBLISH_WINDOW_SECONDS", "60")
            ),
            admin_archive_rate_limit_max=int(
                os.getenv("COURSE_RATE_LIMIT_ADMIN_ARCHIVE_MAX", "20")
            ),
            admin_archive_rate_limit_window_seconds=int(
                os.getenv("COURSE_RATE_LIMIT_ADMIN_ARCHIVE_WINDOW_SECONDS", "60")
            ),
        )
