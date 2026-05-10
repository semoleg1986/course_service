"""Composition root course_service."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

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
from src.infrastructure.bonus.http_bonus_wallet import HttpBonusWalletPort
from src.infrastructure.bonus.inmemory_bonus_wallet import InMemoryBonusWalletPort
from src.infrastructure.clock.system_clock import SystemClock
from src.infrastructure.config.settings import Settings
from src.infrastructure.db.inmemory.access_read_model import InMemoryAccessReadModel
from src.infrastructure.db.inmemory.audit_evidence_repository import (
    InMemoryAuditEvidenceRepository,
)
from src.infrastructure.db.inmemory.course_repository import InMemoryCourseRepository
from src.infrastructure.db.inmemory.outbox_repository import InMemoryOutboxRepository
from src.infrastructure.db.inmemory.uow import InMemoryUnitOfWork
from src.infrastructure.users.inmemory_parent_student_relation_checker import (
    InMemoryParentStudentRelationChecker,
)
from src.infrastructure.users.inmemory_student_parent_directory import (
    InMemoryStudentParentDirectory,
)
from src.infrastructure.users.inmemory_teacher_directory import InMemoryTeacherDirectory
from src.infrastructure.users.users_service_parent_student_relation_checker import (
    UsersServiceParentStudentRelationChecker,
)
from src.infrastructure.users.users_service_student_parent_directory import (
    UsersServiceStudentParentDirectory,
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
    audit_repo: object
    bonus_wallet: object
    outbox_repo: object
    bonus_outbox_dispatcher: Callable[..., None]


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
        audit_repo = InMemoryAuditEvidenceRepository()
        outbox_repo = InMemoryOutboxRepository()
        teacher_directory = InMemoryTeacherDirectory()
        relation_checker = InMemoryParentStudentRelationChecker()
        student_parent_directory = InMemoryStudentParentDirectory()
        bonus_wallet = InMemoryBonusWalletPort()
    else:
        from src.infrastructure.db.sqlalchemy import (
            audit_evidence_repository_sqlalchemy as audit_repo_sqlalchemy,
        )
        from src.infrastructure.db.sqlalchemy import models as _models  # noqa: F401
        from src.infrastructure.db.sqlalchemy.access_read_model_sqlalchemy import (
            SqlalchemyAccessReadModel,
        )
        from src.infrastructure.db.sqlalchemy.base import Base
        from src.infrastructure.db.sqlalchemy.course_repository_sqlalchemy import (
            SqlalchemyCourseRepository,
        )
        from src.infrastructure.db.sqlalchemy.outbox_repository_sqlalchemy import (
            SqlalchemyOutboxRepository,
        )
        from src.infrastructure.db.sqlalchemy.session import (
            build_engine,
            build_session_factory,
        )
        from src.infrastructure.db.sqlalchemy.uow import SqlalchemyUnitOfWork

        engine = build_engine(settings.database_url)
        if settings.auto_create_schema:
            Base.metadata.create_all(bind=engine)
        session_factory = build_session_factory(engine)
        read_model = SqlalchemyAccessReadModel(session_factory)
        course_repository = SqlalchemyCourseRepository(session_factory)
        audit_repo = audit_repo_sqlalchemy.SqlalchemyAuditEvidenceRepository(
            session_factory
        )
        outbox_repo = SqlalchemyOutboxRepository(session_factory)
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
        student_parent_directory = UsersServiceStudentParentDirectory(
            base_url=settings.users_service_base_url,
            service_token=settings.users_service_token,
            timeout_seconds=settings.users_service_timeout_seconds,
        )
        bonus_wallet = HttpBonusWalletPort(
            base_url=settings.bonus_service_base_url,
            service_token=settings.bonus_service_token,
            timeout_seconds=settings.bonus_service_timeout_seconds,
        )

        def build_sql_uow():
            return SqlalchemyUnitOfWork(session_factory)

        uow_factory = build_sql_uow

    if settings.use_inmemory:

        def build_inmemory_uow():
            return InMemoryUnitOfWork(
                course_repository=course_repository,
                access_read_model=read_model,
                audit_evidence=audit_repo,
                outbox=outbox_repo,
            )

        uow_factory = build_inmemory_uow

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
            uow_factory=uow_factory,
            clock=clock,
            teacher_directory=teacher_directory,
        ),
    )
    facade.register_command_handler(
        AddModuleCommand,
        AddModuleHandler(uow_factory=uow_factory, clock=clock),
    )
    facade.register_command_handler(
        AddLessonCommand,
        AddLessonHandler(uow_factory=uow_factory, clock=clock),
    )
    facade.register_command_handler(
        PublishCourseCommand,
        PublishCourseHandler(uow_factory=uow_factory, clock=clock),
    )
    facade.register_command_handler(
        ArchiveCourseCommand,
        ArchiveCourseHandler(uow_factory=uow_factory, clock=clock),
    )
    facade.register_command_handler(
        UpdateModuleCommand,
        UpdateModuleHandler(uow_factory=uow_factory, clock=clock),
    )
    facade.register_command_handler(
        UpdateLessonCommand,
        UpdateLessonHandler(uow_factory=uow_factory, clock=clock),
    )
    facade.register_command_handler(
        UpdateCourseCommand,
        UpdateCourseHandler(
            uow_factory=uow_factory,
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
    complete_lesson_handler = CompleteLessonHandler(
        read_model=read_model,
        clock=clock,
        check_access_handler=check_access_handler,
        uow_factory=uow_factory,
        student_parent_directory=student_parent_directory,
        bonus_wallet=bonus_wallet,
        bonus_enabled=settings.bonus_enabled,
        course_completion_bonus_points=settings.bonus_course_completion_points,
    )
    facade.register_command_handler(
        CompleteLessonCommand,
        complete_lesson_handler,
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
            clock=clock,
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
        audit_repo=audit_repo,
        bonus_wallet=bonus_wallet,
        outbox_repo=outbox_repo,
        bonus_outbox_dispatcher=(
            complete_lesson_handler.dispatch_pending_bonus_side_effects
        ),
    )
