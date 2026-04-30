"""add course modules and lessons

Revision ID: 20260430_0003
Revises: 20260412_0002
Create Date: 2026-04-30 12:00:00.000000
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "20260430_0003"
down_revision = "20260412_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "course_modules",
        sa.Column("module_id", sa.String(length=36), nullable=False),
        sa.Column("course_id", sa.String(length=36), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_by", sa.String(length=64), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_by", sa.String(length=64), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.ForeignKeyConstraint(
            ["course_id"],
            ["course_catalog.course_id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("module_id"),
    )
    op.create_index(
        "ix_course_modules_course_id", "course_modules", ["course_id"], unique=False
    )

    op.create_table(
        "course_lessons",
        sa.Column("lesson_id", sa.String(length=36), nullable=False),
        sa.Column("module_id", sa.String(length=36), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_by", sa.String(length=64), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_by", sa.String(length=64), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.ForeignKeyConstraint(
            ["module_id"],
            ["course_modules.module_id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("lesson_id"),
    )
    op.create_index(
        "ix_course_lessons_module_id", "course_lessons", ["module_id"], unique=False
    )


def downgrade() -> None:
    op.drop_index("ix_course_lessons_module_id", table_name="course_lessons")
    op.drop_table("course_lessons")
    op.drop_index("ix_course_modules_course_id", table_name="course_modules")
    op.drop_table("course_modules")
