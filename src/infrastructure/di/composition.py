"""Composition root course_service."""

from __future__ import annotations

from dataclasses import dataclass

from src.application.access.handlers.check_course_access_handler import (
    CheckCourseAccessHandler,
)
from src.application.access.queries.dto import CheckCourseAccessQuery
from src.application.courses.commands.dto import (
    CreateCourseCommand,
    UpdateCourseCommand,
)
from src.application.courses.handlers.manage_course_handlers import (
    CreateCourseHandler,
    GetCourseByIdHandler,
    UpdateCourseHandler,
)
from src.application.courses.queries.dto import GetCourseByIdQuery
from src.application.facade.application_facade import ApplicationFacade
from src.application.ports.access_token_verifier import AccessTokenVerifier
from src.infrastructure.auth.jwks_access_token_verifier import JwksAccessTokenVerifier
from src.infrastructure.clock.system_clock import SystemClock
from src.infrastructure.config.settings import Settings
from src.infrastructure.db.inmemory.access_read_model import InMemoryAccessReadModel
from src.infrastructure.db.inmemory.course_repository import InMemoryCourseRepository
from src.infrastructure.users.inmemory_teacher_directory import InMemoryTeacherDirectory
from src.infrastructure.users.users_service_teacher_directory import (
    UsersServiceTeacherDirectory,
)


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
        audience=settings.auth_audience,
        jwks_url=settings.auth_jwks_url,
        jwks_json=settings.auth_jwks_json,
    )

    if settings.use_inmemory:
        read_model = InMemoryAccessReadModel()
        course_repository = InMemoryCourseRepository()
        teacher_directory = InMemoryTeacherDirectory()
    else:
        from src.infrastructure.db.sqlalchemy import models as _models  # noqa: F401
        from src.infrastructure.db.sqlalchemy.access_read_model_sqlalchemy import (
            SqlalchemyAccessReadModel,
        )
        from src.infrastructure.db.sqlalchemy.base import Base
        from src.infrastructure.db.sqlalchemy.course_repository_sqlalchemy import (
            SqlalchemyCourseRepository,
        )
        from src.infrastructure.db.sqlalchemy.session import (
            build_engine,
            build_session_factory,
        )

        engine = build_engine(settings.database_url)
        if settings.auto_create_schema:
            Base.metadata.create_all(bind=engine)
        session_factory = build_session_factory(engine)
        read_model = SqlalchemyAccessReadModel(session_factory)
        course_repository = SqlalchemyCourseRepository(session_factory)
        teacher_directory = UsersServiceTeacherDirectory(
            base_url=settings.users_service_base_url,
            service_token=settings.users_service_token,
            timeout_seconds=settings.users_service_timeout_seconds,
        )

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
    facade.register_command_handler(
        CreateCourseCommand,
        CreateCourseHandler(
            repository=course_repository,
            clock=clock,
            teacher_directory=teacher_directory,
        ),
    )
    facade.register_command_handler(
        UpdateCourseCommand,
        UpdateCourseHandler(
            repository=course_repository,
            clock=clock,
            teacher_directory=teacher_directory,
        ),
    )
    facade.register_query_handler(
        GetCourseByIdQuery,
        GetCourseByIdHandler(repository=course_repository),
    )
    facade.register_query_handler(
        CheckCourseAccessQuery,
        CheckCourseAccessHandler(read_model=read_model, clock=clock),
    )
    return RuntimeContainer(
        facade=facade,
        service_token=settings.service_token,
        access_token_verifier=access_token_verifier,
    )
