"""Composition root course_service."""

from __future__ import annotations

from dataclasses import dataclass

from src.application.ports.access_token_verifier import AccessTokenVerifier
from src.application.access.handlers.check_course_access_handler import (
    CheckCourseAccessHandler,
)
from src.application.access.queries.dto import CheckCourseAccessQuery
from src.application.facade.application_facade import ApplicationFacade
from src.infrastructure.auth.jwks_access_token_verifier import JwksAccessTokenVerifier
from src.infrastructure.clock.system_clock import SystemClock
from src.infrastructure.config.settings import Settings
from src.infrastructure.db.inmemory.access_read_model import InMemoryAccessReadModel


@dataclass(frozen=True, slots=True)
class RuntimeContainer:
    """Контейнер runtime-зависимостей."""

    facade: ApplicationFacade
    service_token: str
    access_token_verifier: AccessTokenVerifier


def build_runtime() -> RuntimeContainer:
    """Собирает runtime-граф зависимостей."""

    settings = Settings.from_env()
    clock = SystemClock()
    access_token_verifier = JwksAccessTokenVerifier(
        issuer=settings.auth_issuer,
        jwks_url=settings.auth_jwks_url,
        jwks_json=settings.auth_jwks_json,
    )

    if settings.use_inmemory:
        read_model = InMemoryAccessReadModel()
    else:
        from src.infrastructure.db.sqlalchemy.base import Base
        from src.infrastructure.db.sqlalchemy.session import build_engine, build_session_factory
        from src.infrastructure.db.sqlalchemy.access_read_model_sqlalchemy import (
            SqlalchemyAccessReadModel,
        )

        engine = build_engine(settings.database_url)
        if settings.auto_create_schema:
            Base.metadata.create_all(bind=engine)
        read_model = SqlalchemyAccessReadModel(build_session_factory(engine))

    # Demo-данные для локальной проверки контракта.
    read_model.seed_course_owner(
        course_id="00000000-0000-0000-0000-000000000001",
        owner_account_id="teacher-1",
    )
    read_model.seed_access_grant_status(
        course_id="00000000-0000-0000-0000-000000000001",
        student_id="student-1",
        status="approved",
    )
    read_model.seed_enrollment_status(
        course_id="00000000-0000-0000-0000-000000000001",
        student_id="student-1",
        status="active",
    )

    facade = ApplicationFacade()
    facade.register_query_handler(
        CheckCourseAccessQuery,
        CheckCourseAccessHandler(read_model=read_model, clock=clock),
    )
    return RuntimeContainer(
        facade=facade,
        service_token=settings.service_token,
        access_token_verifier=access_token_verifier,
    )
