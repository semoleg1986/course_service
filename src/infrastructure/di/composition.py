"""Composition root course_service."""

from __future__ import annotations

from dataclasses import dataclass

from src.application.access.commands.dto import ApplyAccessGrantedEventCommand
from src.application.access.handlers.access_event_handlers import (
    ApplyAccessGrantedEventHandler,
)
from src.application.access.handlers.check_course_access_handler import (
    CheckCourseAccessHandler,
)
from src.application.access.handlers.parent_progress_handlers import (
    ListParentStudentCompletedCoursesHandler,
    ListParentStudentCourseProgressHandler,
)
from src.application.access.queries.dto import (
    CheckCourseAccessQuery,
    ListParentStudentCompletedCoursesQuery,
    ListParentStudentCourseProgressQuery,
)
from src.application.courses.commands.dto import (
    AddLessonCommand,
    AddModuleCommand,
    ArchiveCourseCommand,
    CreateCourseCommand,
    PublishCourseCommand,
    UpdateCourseCommand,
    UpdateLessonCommand,
    UpdateModuleCommand,
)
from src.application.courses.handlers.manage_course_handlers import (
    AddLessonHandler,
    AddModuleHandler,
    ArchiveCourseHandler,
    CreateCourseHandler,
    GetCourseByIdHandler,
    GetPublishedCourseBySlugHandler,
    PublishCourseHandler,
    UpdateCourseHandler,
    UpdateLessonHandler,
    UpdateModuleHandler,
)
from src.application.courses.queries.dto import (
    GetCourseByIdQuery,
    GetPublishedCourseBySlugQuery,
)
from src.application.facade.application_facade import ApplicationFacade
from src.application.learning.commands.dto import CompleteLessonCommand
from src.application.learning.handlers.progress_handlers import (
    CompleteLessonHandler,
    GetStudentCourseProgressHandler,
)
from src.application.learning.queries.dto import GetStudentCourseProgressQuery
from src.application.ports.access_read_model import AccessReadModel
from src.application.ports.access_token_verifier import AccessTokenVerifier
from src.infrastructure.auth.jwks_access_token_verifier import JwksAccessTokenVerifier
from src.infrastructure.clock.system_clock import SystemClock
from src.infrastructure.config.settings import Settings
from src.infrastructure.db.inmemory.access_read_model import InMemoryAccessReadModel
from src.infrastructure.db.inmemory.course_repository import InMemoryCourseRepository
from src.infrastructure.users.inmemory_parent_student_relation_checker import (
    InMemoryParentStudentRelationChecker,
)
from src.infrastructure.users.inmemory_teacher_directory import InMemoryTeacherDirectory
from src.infrastructure.users.users_service_parent_student_relation_checker import (
    UsersServiceParentStudentRelationChecker,
)
from src.infrastructure.users.users_service_teacher_directory import (
    UsersServiceTeacherDirectory,
)


@dataclass(frozen=True, slots=True)
class RuntimeContainer:
    """Контейнер runtime-зависимостей."""

    facade: ApplicationFacade
    service_token: str
    access_token_verifier: AccessTokenVerifier
    access_read_model: AccessReadModel


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
        relation_checker = InMemoryParentStudentRelationChecker()
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
        relation_checker = UsersServiceParentStudentRelationChecker(
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
        AddModuleCommand,
        AddModuleHandler(repository=course_repository, clock=clock),
    )
    facade.register_command_handler(
        AddLessonCommand,
        AddLessonHandler(repository=course_repository, clock=clock),
    )
    facade.register_command_handler(
        PublishCourseCommand,
        PublishCourseHandler(repository=course_repository, clock=clock),
    )
    facade.register_command_handler(
        ArchiveCourseCommand,
        ArchiveCourseHandler(repository=course_repository, clock=clock),
    )
    facade.register_command_handler(
        UpdateModuleCommand,
        UpdateModuleHandler(repository=course_repository, clock=clock),
    )
    facade.register_command_handler(
        UpdateLessonCommand,
        UpdateLessonHandler(repository=course_repository, clock=clock),
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
        GetPublishedCourseBySlugQuery,
        GetPublishedCourseBySlugHandler(repository=course_repository),
    )
    check_access_handler = CheckCourseAccessHandler(read_model=read_model, clock=clock)
    facade.register_query_handler(CheckCourseAccessQuery, check_access_handler)
    facade.register_command_handler(
        ApplyAccessGrantedEventCommand,
        ApplyAccessGrantedEventHandler(read_model=read_model),
    )
    facade.register_command_handler(
        CompleteLessonCommand,
        CompleteLessonHandler(
            course_repository=course_repository,
            read_model=read_model,
            clock=clock,
            check_access_handler=check_access_handler,
        ),
    )
    facade.register_query_handler(
        GetStudentCourseProgressQuery,
        GetStudentCourseProgressHandler(
            course_repository=course_repository,
            read_model=read_model,
            clock=clock,
            check_access_handler=check_access_handler,
        ),
    )
    facade.register_query_handler(
        ListParentStudentCourseProgressQuery,
        ListParentStudentCourseProgressHandler(
            read_model=read_model,
            course_repository=course_repository,
            relation_checker=relation_checker,
        ),
    )
    facade.register_query_handler(
        ListParentStudentCompletedCoursesQuery,
        ListParentStudentCompletedCoursesHandler(
            read_model=read_model,
            course_repository=course_repository,
            relation_checker=relation_checker,
            clock=clock,
        ),
    )
    return RuntimeContainer(
        facade=facade,
        service_token=settings.service_token,
        access_token_verifier=access_token_verifier,
        access_read_model=read_model,
    )
