"""extend module lesson fields

Revision ID: 20260430_0004
Revises: 20260430_0003
Create Date: 2026-04-30 14:00:00.000000
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "20260430_0004"
down_revision = "20260430_0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("course_modules", sa.Column("description", sa.Text(), nullable=True))
    op.add_column(
        "course_modules",
        sa.Column(
            "is_required", sa.Boolean(), nullable=False, server_default=sa.text("true")
        ),
    )
    op.add_column(
        "course_modules",
        sa.Column("released_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "course_modules",
        sa.Column(
            "status", sa.String(length=16), nullable=False, server_default="draft"
        ),
    )
    op.create_index(
        "ix_course_modules_status", "course_modules", ["status"], unique=False
    )

    op.add_column("course_lessons", sa.Column("description", sa.Text(), nullable=True))
    op.add_column(
        "course_lessons",
        sa.Column(
            "content_type", sa.String(length=16), nullable=False, server_default="video"
        ),
    )
    op.add_column("course_lessons", sa.Column("content_ref", sa.Text(), nullable=True))
    op.add_column(
        "course_lessons", sa.Column("duration_minutes", sa.Integer(), nullable=True)
    )
    op.add_column(
        "course_lessons",
        sa.Column(
            "is_preview", sa.Boolean(), nullable=False, server_default=sa.text("false")
        ),
    )
    op.add_column(
        "course_lessons",
        sa.Column("released_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "course_lessons",
        sa.Column(
            "status", sa.String(length=16), nullable=False, server_default="draft"
        ),
    )
    op.create_index(
        "ix_course_lessons_status", "course_lessons", ["status"], unique=False
    )


def downgrade() -> None:
    op.drop_index("ix_course_lessons_status", table_name="course_lessons")
    op.drop_column("course_lessons", "status")
    op.drop_column("course_lessons", "released_at")
    op.drop_column("course_lessons", "is_preview")
    op.drop_column("course_lessons", "duration_minutes")
    op.drop_column("course_lessons", "content_ref")
    op.drop_column("course_lessons", "content_type")
    op.drop_column("course_lessons", "description")

    op.drop_index("ix_course_modules_status", table_name="course_modules")
    op.drop_column("course_modules", "status")
    op.drop_column("course_modules", "released_at")
    op.drop_column("course_modules", "is_required")
    op.drop_column("course_modules", "description")
