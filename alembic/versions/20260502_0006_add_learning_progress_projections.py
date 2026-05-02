"""add learning progress projections

Revision ID: 20260502_0006
Revises: 20260501_0005
Create Date: 2026-05-02 17:35:00
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "20260502_0006"
down_revision = "20260501_0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "lesson_progress_projections",
        sa.Column("course_id", sa.String(length=36), nullable=False),
        sa.Column("module_id", sa.String(length=36), nullable=False),
        sa.Column("lesson_id", sa.String(length=36), nullable=False),
        sa.Column("student_id", sa.String(length=64), nullable=False),
        sa.Column("progress_id", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_by", sa.String(length=64), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_by", sa.String(length=64), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_activity_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("course_id", "student_id", "lesson_id"),
    )
    op.create_index(
        "ix_lesson_progress_projections_course_id",
        "lesson_progress_projections",
        ["course_id"],
        unique=False,
    )
    op.create_index(
        "ix_lesson_progress_projections_module_id",
        "lesson_progress_projections",
        ["module_id"],
        unique=False,
    )
    op.create_index(
        "ix_lesson_progress_projections_lesson_id",
        "lesson_progress_projections",
        ["lesson_id"],
        unique=False,
    )
    op.create_index(
        "ix_lesson_progress_projections_student_id",
        "lesson_progress_projections",
        ["student_id"],
        unique=False,
    )
    op.create_index(
        "ix_lesson_progress_projections_progress_id",
        "lesson_progress_projections",
        ["progress_id"],
        unique=False,
    )
    op.create_index(
        "ix_lesson_progress_projections_status",
        "lesson_progress_projections",
        ["status"],
        unique=False,
    )

    op.create_table(
        "course_progress_projections",
        sa.Column("course_id", sa.String(length=36), nullable=False),
        sa.Column("student_id", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("progress_percent", sa.Numeric(5, 2), nullable=False),
        sa.Column(
            "completed_lessons", sa.Integer(), nullable=False, server_default="0"
        ),
        sa.Column("total_lessons", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("course_id", "student_id"),
    )
    op.create_index(
        "ix_course_progress_projections_course_id",
        "course_progress_projections",
        ["course_id"],
        unique=False,
    )
    op.create_index(
        "ix_course_progress_projections_student_id",
        "course_progress_projections",
        ["student_id"],
        unique=False,
    )
    op.create_index(
        "ix_course_progress_projections_status",
        "course_progress_projections",
        ["status"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_course_progress_projections_status",
        table_name="course_progress_projections",
    )
    op.drop_index(
        "ix_course_progress_projections_student_id",
        table_name="course_progress_projections",
    )
    op.drop_index(
        "ix_course_progress_projections_course_id",
        table_name="course_progress_projections",
    )
    op.drop_table("course_progress_projections")

    op.drop_index(
        "ix_lesson_progress_projections_status",
        table_name="lesson_progress_projections",
    )
    op.drop_index(
        "ix_lesson_progress_projections_progress_id",
        table_name="lesson_progress_projections",
    )
    op.drop_index(
        "ix_lesson_progress_projections_student_id",
        table_name="lesson_progress_projections",
    )
    op.drop_index(
        "ix_lesson_progress_projections_lesson_id",
        table_name="lesson_progress_projections",
    )
    op.drop_index(
        "ix_lesson_progress_projections_module_id",
        table_name="lesson_progress_projections",
    )
    op.drop_index(
        "ix_lesson_progress_projections_course_id",
        table_name="lesson_progress_projections",
    )
    op.drop_table("lesson_progress_projections")
