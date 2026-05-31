from __future__ import annotations

import json
from uuid import uuid4

from src.application.access.queries.dto import CheckCourseAccessQuery
from src.application.common.dto import (
    StudentCourseLearningLessonResult,
    StudentCourseLearningModuleResult,
    StudentCourseLearningProgressResult,
    StudentCourseLearningResult,
    StudentCourseProgressResult,
    StudentLessonCompletionResult,
)
from src.application.learning.commands.dto import CompleteLessonCommand
from src.application.learning.progress_summary import evaluate_course_progress_summary
from src.application.learning.queries.dto import (
    GetStudentCourseLearningQuery,
    GetStudentCourseProgressQuery,
)
from src.application.ports.access_read_model import AccessReadModel
from src.application.ports.bonus_wallet import BonusWalletPort
from src.application.ports.clock import Clock
from src.application.ports.outbox import (
    OutboxEventRecord,
    OutboxEventStatus,
    OutboxEventType,
)
from src.application.ports.student_parent_directory import StudentParentDirectory
from src.application.ports.unit_of_work import UnitOfWork
from src.domain.content.course.entity import Course, Lesson, Module
from src.domain.content.course.repository import CourseRepository
from src.domain.errors import AccessDeniedError, InvariantViolationError, NotFoundError
from src.domain.learning.lesson_progress.entity import LessonProgress
from src.domain.shared.statuses import LessonProgressStatus, PublishState


class CompleteLessonHandler:
    """Отмечает урок завершенным и пересчитывает course progress."""

    def __init__(
        self,
        *,
        read_model: AccessReadModel,
        clock: Clock,
        check_access_handler,
        uow_factory,
        student_parent_directory: StudentParentDirectory,
        bonus_wallet: BonusWalletPort,
        bonus_enabled: bool,
        course_completion_bonus_points: int,
    ) -> None:
        self._read_model = read_model
        self._clock = clock
        self._check_access_handler = check_access_handler
        self._uow_factory = uow_factory
        self._student_parent_directory = student_parent_directory
        self._bonus_wallet = bonus_wallet
        self._bonus_enabled = bonus_enabled
        self._course_completion_bonus_points = course_completion_bonus_points

    def __call__(self, command: CompleteLessonCommand) -> StudentLessonCompletionResult:
        role_set = {
            role.strip().lower() for role in command.actor_roles if role.strip()
        }
        if "student" not in role_set:
            raise AccessDeniedError("Операция доступна только student.")

        decision = self._check_access_handler(
            CheckCourseAccessQuery(
                course_id=command.course_id,
                actor_account_id=command.actor_id,
                actor_roles=command.actor_roles,
                student_id=command.actor_id,
                require_active_grant=True,
                require_enrollment=False,
            )
        )
        if decision.decision != "allow":
            raise AccessDeniedError("Нет активного доступа к курсу.")

        now = self._clock.now()
        uow = self._uow_factory()
        try:
            repos = uow.repositories
            course = repos.courses.get(command.course_id)
            if course is None:
                raise NotFoundError("Курс не найден.")

            module, lesson, lesson_exists = self._find_lesson_for_completion(
                course, command.lesson_id
            )
            if module is None or lesson is None:
                if lesson_exists:
                    raise InvariantViolationError(
                        "Урок существует, но пока недоступен для прохождения."
                    )
                raise NotFoundError("Урок не найден.")

            previous_summary = repos.access_read_model.get_course_progress_summary(
                course_id=command.course_id,
                student_id=command.actor_id,
            )
            existing = repos.access_read_model.get_lesson_progress(
                course_id=command.course_id,
                student_id=command.actor_id,
                lesson_id=command.lesson_id,
            )
            if existing is None:
                progress = LessonProgress.create(
                    progress_id=str(uuid4()),
                    course_id=command.course_id,
                    module_id=module.module_id,
                    lesson_id=command.lesson_id,
                    student_id=command.actor_id,
                    created_at=now,
                    created_by=command.actor_id,
                )
            else:
                progress = LessonProgress.restore(
                    progress_id=str(existing["progress_id"]),
                    course_id=command.course_id,
                    module_id=module.module_id,
                    lesson_id=command.lesson_id,
                    student_id=command.actor_id,
                    status=LessonProgressStatus(str(existing["status"])),
                    created_at=existing["created_at"],
                    created_by=str(existing["created_by"]),
                    updated_at=existing["updated_at"],
                    updated_by=str(existing["updated_by"]),
                    version=int(existing["version"]),
                    started_at=existing["started_at"],
                    completed_at=existing["completed_at"],
                    last_activity_at=existing["last_activity_at"],
                )

            progress.complete(changed_at=now, changed_by=command.actor_id)
            repos.access_read_model.upsert_lesson_progress(
                course_id=progress.course_id,
                module_id=progress.module_id,
                lesson_id=progress.lesson_id,
                student_id=progress.student_id,
                progress_id=progress.progress_id,
                status=progress.status.value,
                created_at=progress.meta.created_at,
                created_by=progress.meta.created_by,
                updated_at=progress.meta.updated_at,
                updated_by=progress.meta.updated_by,
                version=progress.meta.version,
                started_at=progress.started_at,
                completed_at=progress.completed_at,
                last_activity_at=progress.last_activity_at,
            )

            summary = evaluate_course_progress_summary(
                course=course,
                student_id=command.actor_id,
                read_model=repos.access_read_model,
                evaluated_at=now,
            )
            if self._should_accrue_course_completion_bonus(
                previous_status=(
                    previous_summary[0] if previous_summary is not None else None
                ),
                new_status=summary.status.value,
            ):
                self._enqueue_course_completion_bonus(
                    uow=uow,
                    course_id=command.course_id,
                    student_id=command.actor_id,
                    occurred_at=now,
                )
            repos.access_read_model.store_course_progress_summary(
                course_id=command.course_id,
                student_id=command.actor_id,
                status=summary.status.value,
                progress_percent=summary.progress_percent,
                completed_lessons=summary.completed_lessons,
                total_lessons=summary.total_lessons,
                completed_at=summary.completed_at,
            )
            uow.commit()
        except Exception:
            uow.rollback()
            raise
        finally:
            uow.close()

        self.dispatch_pending_bonus_side_effects()
        return StudentLessonCompletionResult(
            course_id=command.course_id,
            module_id=module.module_id,
            lesson_id=command.lesson_id,
            student_id=command.actor_id,
            lesson_status=progress.status.value,
            course_status=summary.status.value,
            progress_percent=summary.progress_percent,
            completed_lessons=summary.completed_lessons,
            total_lessons=summary.total_lessons,
            completed_at=summary.completed_at,
        )

    def _should_accrue_course_completion_bonus(
        self, *, previous_status: str | None, new_status: str
    ) -> bool:
        return (
            self._bonus_enabled
            and self._course_completion_bonus_points > 0
            and previous_status != "completed"
            and new_status == "completed"
        )

    def _enqueue_course_completion_bonus(
        self, *, uow: UnitOfWork, course_id: str, student_id: str, occurred_at
    ) -> None:
        reference_id = f"course-completed:{course_id}:{student_id}"
        parent_ids = self._student_parent_directory.list_parent_ids(student_id)
        for parent_id in sorted({item.strip() for item in parent_ids if item.strip()}):
            aggregate_id = f"{course_id}:{student_id}:{parent_id}"
            uow.repositories.outbox.add(
                OutboxEventRecord(
                    event_id=str(uuid4()),
                    aggregate_type="course_completion",
                    aggregate_id=aggregate_id,
                    event_type=OutboxEventType.COURSE_COMPLETION_BONUS_ACCRUAL,
                    payload_json=json.dumps(
                        {
                            "parent_id": parent_id,
                            "amount": self._course_completion_bonus_points,
                            "reason_code": "course_completed_reward",
                            "reference_id": reference_id,
                            "idempotency_key": f"{reference_id}:{parent_id}",
                        },
                        ensure_ascii=True,
                        sort_keys=True,
                    ),
                    status=OutboxEventStatus.PENDING,
                    attempt_count=0,
                    available_at=occurred_at,
                    created_at=occurred_at,
                )
            )

    def dispatch_pending_bonus_side_effects(self, *, limit: int = 100) -> None:
        read_uow = self._uow_factory()
        try:
            events = read_uow.repositories.outbox.list_pending(limit=limit)
        finally:
            read_uow.close()

        for event in events:
            try:
                payload = json.loads(event.payload_json)
                self._bonus_wallet.accrue(
                    parent_id=payload["parent_id"],
                    amount=int(payload["amount"]),
                    reason_code=payload["reason_code"],
                    reference_id=payload["reference_id"],
                    idempotency_key=payload["idempotency_key"],
                )
            except Exception as exc:
                uow = self._uow_factory()
                try:
                    uow.repositories.outbox.save(event.mark_failed(error=str(exc)))
                    uow.commit()
                finally:
                    uow.close()
            else:
                uow = self._uow_factory()
                try:
                    uow.repositories.outbox.save(
                        event.mark_processed(at=self._clock.now())
                    )
                    uow.commit()
                finally:
                    uow.close()

    @staticmethod
    def _find_lesson_for_completion(
        course: Course, lesson_id: str
    ) -> tuple[Module | None, Lesson | None, bool]:
        lesson_exists = False
        for module in course.modules:
            module_matches = False
            if module.status.value != "published":
                for lesson in module.lessons:
                    if lesson.lesson_id == lesson_id:
                        lesson_exists = True
                continue
            for lesson in module.lessons:
                if lesson.lesson_id != lesson_id:
                    continue
                lesson_exists = True
                module_matches = True
                if lesson.status.value == "published":
                    return module, lesson, True
            if module_matches:
                break
        return None, None, lesson_exists


class GetStudentCourseProgressHandler:
    """Возвращает агрегированный прогресс текущего студента по курсу."""

    def __init__(
        self,
        *,
        course_repository: CourseRepository,
        read_model: AccessReadModel,
        clock: Clock,
        check_access_handler,
    ) -> None:
        self._course_repository = course_repository
        self._read_model = read_model
        self._clock = clock
        self._check_access_handler = check_access_handler

    def __call__(
        self, query: GetStudentCourseProgressQuery
    ) -> StudentCourseProgressResult:
        role_set = {role.strip().lower() for role in query.actor_roles if role.strip()}
        if "student" not in role_set:
            raise AccessDeniedError("Операция доступна только student.")

        course = self._course_repository.get(query.course_id)
        if course is None:
            raise NotFoundError("Курс не найден.")

        decision = self._check_access_handler(
            CheckCourseAccessQuery(
                course_id=query.course_id,
                actor_account_id=query.actor_id,
                actor_roles=query.actor_roles,
                student_id=query.actor_id,
                require_active_grant=True,
                require_enrollment=False,
            )
        )
        if decision.decision != "allow":
            raise AccessDeniedError("Нет активного доступа к курсу.")

        summary = self._read_model.get_course_progress_summary(
            course_id=query.course_id,
            student_id=query.actor_id,
        )
        if summary is None:
            computed = evaluate_course_progress_summary(
                course=course,
                student_id=query.actor_id,
                read_model=self._read_model,
                evaluated_at=self._clock.now(),
            )
            self._read_model.store_course_progress_summary(
                course_id=query.course_id,
                student_id=query.actor_id,
                status=computed.status.value,
                progress_percent=computed.progress_percent,
                completed_lessons=computed.completed_lessons,
                total_lessons=computed.total_lessons,
                completed_at=computed.completed_at,
            )
            return StudentCourseProgressResult(
                course_id=query.course_id,
                title=course.title,
                progress_percent=computed.progress_percent,
                completed_lessons=computed.completed_lessons,
                total_lessons=computed.total_lessons,
                status=computed.status.value,
                completed_at=computed.completed_at,
            )

        status, progress_percent, completed_lessons, total_lessons, completed_at = (
            summary
        )
        return StudentCourseProgressResult(
            course_id=query.course_id,
            title=course.title,
            progress_percent=progress_percent,
            completed_lessons=completed_lessons,
            total_lessons=total_lessons,
            status=status,
            completed_at=completed_at,
        )


class GetStudentCourseLearningHandler:
    """Возвращает student-facing read model курса с уроками и прогрессом."""

    def __init__(
        self,
        *,
        course_repository: CourseRepository,
        read_model: AccessReadModel,
        clock: Clock,
        check_access_handler,
    ) -> None:
        self._course_repository = course_repository
        self._read_model = read_model
        self._clock = clock
        self._check_access_handler = check_access_handler

    def __call__(
        self, query: GetStudentCourseLearningQuery
    ) -> StudentCourseLearningResult:
        role_set = {role.strip().lower() for role in query.actor_roles if role.strip()}
        if "student" not in role_set:
            raise AccessDeniedError("Операция доступна только student.")

        course = self._course_repository.get(query.course_id)
        if course is None:
            raise NotFoundError("Курс не найден.")
        if course.publish_state != PublishState.PUBLISHED:
            raise AccessDeniedError("Курс недоступен для обучения.")

        decision = self._check_access_handler(
            CheckCourseAccessQuery(
                course_id=query.course_id,
                actor_account_id=query.actor_id,
                actor_roles=query.actor_roles,
                student_id=query.actor_id,
                require_active_grant=True,
                require_enrollment=False,
            )
        )
        if decision.decision != "allow":
            raise AccessDeniedError("Нет активного доступа к курсу.")

        summary = self._get_or_compute_summary(course=course, student_id=query.actor_id)
        completed_lesson_ids = set(
            self._read_model.list_completed_lesson_ids(
                course_id=query.course_id,
                student_id=query.actor_id,
            )
        )
        modules = self._build_modules(
            course=course,
            student_id=query.actor_id,
            completed_lesson_ids=completed_lesson_ids,
        )
        next_lesson_id = self._find_next_lesson_id(modules)

        return StudentCourseLearningResult(
            course_id=query.course_id,
            title=course.title,
            description=course.description,
            level=course.audience.level,
            progress=StudentCourseLearningProgressResult(
                progress_percent=summary.progress_percent,
                completed_lessons=summary.completed_lessons,
                total_lessons=summary.total_lessons,
                status=summary.status,
                completed_at=summary.completed_at,
            ),
            next_lesson_id=next_lesson_id,
            modules=modules,
        )

    def _get_or_compute_summary(
        self, *, course: Course, student_id: str
    ) -> StudentCourseLearningProgressResult:
        summary = self._read_model.get_course_progress_summary(
            course_id=course.course_id,
            student_id=student_id,
        )
        if summary is not None:
            status, progress_percent, completed_lessons, total_lessons, completed_at = (
                summary
            )
            return StudentCourseLearningProgressResult(
                progress_percent=progress_percent,
                completed_lessons=completed_lessons,
                total_lessons=total_lessons,
                status=status,
                completed_at=completed_at,
            )

        computed = evaluate_course_progress_summary(
            course=course,
            student_id=student_id,
            read_model=self._read_model,
            evaluated_at=self._clock.now(),
        )
        self._read_model.store_course_progress_summary(
            course_id=course.course_id,
            student_id=student_id,
            status=computed.status.value,
            progress_percent=computed.progress_percent,
            completed_lessons=computed.completed_lessons,
            total_lessons=computed.total_lessons,
            completed_at=computed.completed_at,
        )
        return StudentCourseLearningProgressResult(
            progress_percent=computed.progress_percent,
            completed_lessons=computed.completed_lessons,
            total_lessons=computed.total_lessons,
            status=computed.status.value,
            completed_at=computed.completed_at,
        )

    def _build_modules(
        self,
        *,
        course: Course,
        student_id: str,
        completed_lesson_ids: set[str],
    ) -> list[StudentCourseLearningModuleResult]:
        modules: list[StudentCourseLearningModuleResult] = []
        for module in course.modules:
            if module.status != PublishState.PUBLISHED:
                continue
            lessons: list[StudentCourseLearningLessonResult] = []
            for lesson in module.lessons:
                if lesson.status != PublishState.PUBLISHED:
                    continue
                lesson_progress = self._read_model.get_lesson_progress(
                    course_id=course.course_id,
                    student_id=student_id,
                    lesson_id=lesson.lesson_id,
                )
                progress_status = (
                    str(lesson_progress.get("status"))
                    if lesson_progress is not None
                    else "not_started"
                )
                is_completed = lesson.lesson_id in completed_lesson_ids
                lessons.append(
                    StudentCourseLearningLessonResult(
                        lesson_id=lesson.lesson_id,
                        title=lesson.title,
                        description=lesson.description,
                        content_type=lesson.content_type,
                        content_ref=lesson.content_ref,
                        duration_minutes=lesson.duration_minutes,
                        is_preview=lesson.is_preview,
                        progress_status=progress_status,
                        is_completed=is_completed,
                    )
                )
            modules.append(
                StudentCourseLearningModuleResult(
                    module_id=module.module_id,
                    title=module.title,
                    description=module.description,
                    is_required=module.is_required,
                    lessons_count=len(lessons),
                    lessons=lessons,
                )
            )
        return modules

    @staticmethod
    def _find_next_lesson_id(
        modules: list[StudentCourseLearningModuleResult],
    ) -> str | None:
        for module in modules:
            for lesson in module.lessons:
                if not lesson.is_completed:
                    return lesson.lesson_id
        return None
