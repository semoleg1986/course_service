"""SQLAlchemy read-model для проверки доступа."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from src.infrastructure.db.sqlalchemy.models import (
    AccessGrantProjectionModel,
    CourseOwnerProjectionModel,
    CourseProgressProjectionModel,
    EnrollmentProjectionModel,
    LessonProgressProjectionModel,
    ProcessedAccessEventModel,
)


class SqlalchemyAccessReadModel:
    """Реализация AccessReadModel поверх SQLAlchemy."""

    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    def get_course_owner(self, course_id: str) -> str | None:
        with self._session_factory() as db:
            row = db.get(CourseOwnerProjectionModel, course_id)
            return row.owner_account_id if row else None

    def get_access_grant_status(self, course_id: str, student_id: str) -> str | None:
        with self._session_factory() as db:
            stmt = select(AccessGrantProjectionModel.status).where(
                AccessGrantProjectionModel.course_id == course_id,
                AccessGrantProjectionModel.student_id == student_id,
            )
            return db.execute(stmt).scalar_one_or_none()

    def get_enrollment_status(self, course_id: str, student_id: str) -> str | None:
        with self._session_factory() as db:
            stmt = select(EnrollmentProjectionModel.status).where(
                EnrollmentProjectionModel.course_id == course_id,
                EnrollmentProjectionModel.student_id == student_id,
            )
            return db.execute(stmt).scalar_one_or_none()

    def list_access_grants_by_student(self, student_id: str) -> list[tuple[str, str]]:
        with self._session_factory() as db:
            stmt = (
                select(
                    AccessGrantProjectionModel.course_id,
                    AccessGrantProjectionModel.status,
                )
                .where(AccessGrantProjectionModel.student_id == student_id)
                .order_by(AccessGrantProjectionModel.course_id.asc())
            )
            rows = db.execute(stmt).all()
            return [(str(course_id), str(status)) for course_id, status in rows]

    def list_enrollments_by_student(self, student_id: str) -> list[tuple[str, str]]:
        with self._session_factory() as db:
            stmt = (
                select(
                    EnrollmentProjectionModel.course_id,
                    EnrollmentProjectionModel.status,
                )
                .where(EnrollmentProjectionModel.student_id == student_id)
                .order_by(EnrollmentProjectionModel.course_id.asc())
            )
            rows = db.execute(stmt).all()
            return [(str(course_id), str(status)) for course_id, status in rows]

    def upsert_lesson_progress(
        self,
        *,
        course_id: str,
        module_id: str,
        lesson_id: str,
        student_id: str,
        progress_id: str,
        status: str,
        created_at,
        created_by: str,
        updated_at,
        updated_by: str,
        version: int,
        started_at,
        completed_at,
        last_activity_at,
    ) -> None:
        with self._session_factory.begin() as db:
            stmt = select(LessonProgressProjectionModel).where(
                LessonProgressProjectionModel.course_id == course_id,
                LessonProgressProjectionModel.student_id == student_id,
                LessonProgressProjectionModel.lesson_id == lesson_id,
            )
            row = db.execute(stmt).scalar_one_or_none()
            if row is None:
                db.add(
                    LessonProgressProjectionModel(
                        course_id=course_id,
                        module_id=module_id,
                        lesson_id=lesson_id,
                        student_id=student_id,
                        progress_id=progress_id,
                        status=status,
                        created_at=created_at,
                        created_by=created_by,
                        updated_at=updated_at,
                        updated_by=updated_by,
                        version=version,
                        started_at=started_at,
                        completed_at=completed_at,
                        last_activity_at=last_activity_at,
                    )
                )
            else:
                row.module_id = module_id
                row.progress_id = progress_id
                row.status = status
                row.created_at = created_at
                row.created_by = created_by
                row.updated_at = updated_at
                row.updated_by = updated_by
                row.version = version
                row.started_at = started_at
                row.completed_at = completed_at
                row.last_activity_at = last_activity_at

    def get_lesson_progress(
        self, *, course_id: str, student_id: str, lesson_id: str
    ) -> dict[str, object] | None:
        with self._session_factory() as db:
            stmt = select(LessonProgressProjectionModel).where(
                LessonProgressProjectionModel.course_id == course_id,
                LessonProgressProjectionModel.student_id == student_id,
                LessonProgressProjectionModel.lesson_id == lesson_id,
            )
            row = db.execute(stmt).scalar_one_or_none()
            if row is None:
                return None
            return {
                "progress_id": row.progress_id,
                "module_id": row.module_id,
                "status": row.status,
                "created_at": self._normalize_datetime(row.created_at),
                "created_by": row.created_by,
                "updated_at": self._normalize_datetime(row.updated_at),
                "updated_by": row.updated_by,
                "version": row.version,
                "started_at": self._normalize_datetime(row.started_at),
                "completed_at": self._normalize_datetime(row.completed_at),
                "last_activity_at": self._normalize_datetime(row.last_activity_at),
            }

    def list_completed_lesson_ids(
        self, *, course_id: str, student_id: str
    ) -> list[str]:
        with self._session_factory() as db:
            stmt = (
                select(LessonProgressProjectionModel.lesson_id)
                .where(
                    LessonProgressProjectionModel.course_id == course_id,
                    LessonProgressProjectionModel.student_id == student_id,
                    LessonProgressProjectionModel.status == "completed",
                )
                .order_by(LessonProgressProjectionModel.lesson_id.asc())
            )
            return [str(lesson_id) for lesson_id in db.execute(stmt).scalars().all()]

    def store_course_progress_summary(
        self,
        *,
        course_id: str,
        student_id: str,
        status: str,
        progress_percent: float,
        completed_lessons: int,
        total_lessons: int,
        completed_at,
    ) -> None:
        with self._session_factory.begin() as db:
            stmt = select(CourseProgressProjectionModel).where(
                CourseProgressProjectionModel.course_id == course_id,
                CourseProgressProjectionModel.student_id == student_id,
            )
            row = db.execute(stmt).scalar_one_or_none()
            if row is None:
                db.add(
                    CourseProgressProjectionModel(
                        course_id=course_id,
                        student_id=student_id,
                        status=status,
                        progress_percent=progress_percent,
                        completed_lessons=completed_lessons,
                        total_lessons=total_lessons,
                        completed_at=completed_at,
                    )
                )
            else:
                row.status = status
                row.progress_percent = progress_percent
                row.completed_lessons = completed_lessons
                row.total_lessons = total_lessons
                row.completed_at = completed_at

    def get_course_progress_summary(
        self, *, course_id: str, student_id: str
    ) -> tuple[str, float, int, int, object | None] | None:
        with self._session_factory() as db:
            stmt = select(CourseProgressProjectionModel).where(
                CourseProgressProjectionModel.course_id == course_id,
                CourseProgressProjectionModel.student_id == student_id,
            )
            row = db.execute(stmt).scalar_one_or_none()
            if row is None:
                return None
            return (
                str(row.status),
                float(row.progress_percent),
                int(row.completed_lessons),
                int(row.total_lessons),
                self._normalize_datetime(row.completed_at),
            )

    @staticmethod
    def _normalize_datetime(value: datetime | None) -> datetime | None:
        if value is None:
            return None
        if value.tzinfo is None or value.utcoffset() is None:
            return value.replace(tzinfo=UTC)
        return value

    def seed_course_owner(self, course_id: str, owner_account_id: str) -> None:
        with self._session_factory.begin() as db:
            row = db.get(CourseOwnerProjectionModel, course_id)
            if row is None:
                db.add(
                    CourseOwnerProjectionModel(
                        course_id=course_id,
                        owner_account_id=owner_account_id,
                    )
                )
            else:
                row.owner_account_id = owner_account_id

    def seed_access_grant_status(
        self, course_id: str, student_id: str, status: str
    ) -> None:
        with self._session_factory.begin() as db:
            stmt = select(AccessGrantProjectionModel).where(
                AccessGrantProjectionModel.course_id == course_id,
                AccessGrantProjectionModel.student_id == student_id,
            )
            row = db.execute(stmt).scalar_one_or_none()
            if row is None:
                db.add(
                    AccessGrantProjectionModel(
                        course_id=course_id,
                        student_id=student_id,
                        status=status,
                    )
                )
            else:
                row.status = status

    def seed_enrollment_status(
        self, course_id: str, student_id: str, status: str
    ) -> None:
        with self._session_factory.begin() as db:
            stmt = select(EnrollmentProjectionModel).where(
                EnrollmentProjectionModel.course_id == course_id,
                EnrollmentProjectionModel.student_id == student_id,
            )
            row = db.execute(stmt).scalar_one_or_none()
            if row is None:
                db.add(
                    EnrollmentProjectionModel(
                        course_id=course_id,
                        student_id=student_id,
                        status=status,
                    )
                )
            else:
                row.status = status

    def apply_access_granted_event(
        self,
        *,
        event_id: str,
        course_id: str,
        student_id: str,
        granted_status: str,
    ) -> bool:
        with self._session_factory.begin() as db:
            processed = db.get(ProcessedAccessEventModel, event_id)
            if processed is not None:
                return False

            stmt = select(AccessGrantProjectionModel).where(
                AccessGrantProjectionModel.course_id == course_id,
                AccessGrantProjectionModel.student_id == student_id,
            )
            row = db.execute(stmt).scalar_one_or_none()
            if row is None:
                db.add(
                    AccessGrantProjectionModel(
                        course_id=course_id,
                        student_id=student_id,
                        status=granted_status,
                    )
                )
            else:
                row.status = granted_status

            db.add(
                ProcessedAccessEventModel(
                    event_id=event_id,
                    course_id=course_id,
                    student_id=student_id,
                )
            )
            return True
