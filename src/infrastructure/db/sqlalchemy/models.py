"""ORM-модели read-model слоя course_service."""

from __future__ import annotations

from sqlalchemy import PrimaryKeyConstraint, String
from sqlalchemy.orm import Mapped, mapped_column

from src.infrastructure.db.sqlalchemy.base import Base


class CourseOwnerProjectionModel(Base):
    """Проекция владельца курса."""

    __tablename__ = "course_owner_projections"

    course_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    owner_account_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)


class AccessGrantProjectionModel(Base):
    """Проекция статуса доступа к курсу."""

    __tablename__ = "access_grant_projections"
    __table_args__ = (PrimaryKeyConstraint("course_id", "student_id"),)

    course_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    student_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, index=True)


class EnrollmentProjectionModel(Base):
    """Проекция статуса enrollment."""

    __tablename__ = "enrollment_projections"
    __table_args__ = (PrimaryKeyConstraint("course_id", "student_id"),)

    course_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    student_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
