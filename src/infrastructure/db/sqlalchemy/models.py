"""ORM-модели read-model слоя course_service."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    PrimaryKeyConstraint,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON

from src.infrastructure.db.sqlalchemy.base import Base


class CourseCatalogModel(Base):
    """Основная проекция курса для write/read API."""

    __tablename__ = "course_catalog"

    course_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    teacher_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    teacher_display_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    slug: Mapped[str] = mapped_column(
        String(255), nullable=False, unique=True, index=True
    )

    starts_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    duration_days: Mapped[int] = mapped_column(Integer, nullable=False)
    access_ttl_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    enrollment_opens_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    enrollment_closes_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    timezone: Mapped[str] = mapped_column(String(64), nullable=False, default="UTC")

    price: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="USD")

    language: Mapped[str] = mapped_column(String(16), nullable=False, default="ru")
    age_min: Mapped[int | None] = mapped_column(Integer, nullable=True)
    age_max: Mapped[int | None] = mapped_column(Integer, nullable=True)
    level: Mapped[str] = mapped_column(String(32), nullable=False, default="beginner")
    max_students: Mapped[int | None] = mapped_column(Integer, nullable=True)

    tags: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    cover_image_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_live_enabled: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    live_room_template_id: Mapped[str | None] = mapped_column(String(64), nullable=True)

    publish_state: Mapped[str] = mapped_column(
        String(32), nullable=False, default="draft", index=True
    )
    published_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    published_by_admin_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    archived_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    archived_by: Mapped[str | None] = mapped_column(String(64), nullable=True)

    seo_meta_title: Mapped[str] = mapped_column(String(70), nullable=False)
    seo_meta_description: Mapped[str] = mapped_column(String(160), nullable=False)
    seo_canonical_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    seo_robots: Mapped[str] = mapped_column(String(16), nullable=False, default="index")
    seo_og_image_url: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    created_by: Mapped[str] = mapped_column(String(64), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    updated_by: Mapped[str] = mapped_column(String(64), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)


class CourseOwnerProjectionModel(Base):
    """Проекция владельца курса."""

    __tablename__ = "course_owner_projections"

    course_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    owner_account_id: Mapped[str] = mapped_column(
        String(64), nullable=False, index=True
    )


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


class CourseModuleModel(Base):
    """Модуль курса."""

    __tablename__ = "course_modules"

    module_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    course_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("course_catalog.course_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    created_by: Mapped[str] = mapped_column(String(64), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    updated_by: Mapped[str] = mapped_column(String(64), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)


class CourseLessonModel(Base):
    """Урок модуля курса."""

    __tablename__ = "course_lessons"

    lesson_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    module_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("course_modules.module_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    created_by: Mapped[str] = mapped_column(String(64), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    updated_by: Mapped[str] = mapped_column(String(64), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
