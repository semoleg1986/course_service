"""SQLAlchemy read-model для проверки доступа."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from src.infrastructure.db.sqlalchemy.models import (
    AccessGrantProjectionModel,
    CourseOwnerProjectionModel,
    EnrollmentProjectionModel,
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
