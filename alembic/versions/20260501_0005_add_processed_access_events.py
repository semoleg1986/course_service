"""add processed access events

Revision ID: 20260501_0005
Revises: 20260430_0004
Create Date: 2026-05-01 19:45:00
"""

from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "20260501_0005"
down_revision = "20260430_0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "processed_access_events",
        sa.Column("event_id", sa.String(length=64), nullable=False),
        sa.Column("course_id", sa.String(length=36), nullable=False),
        sa.Column("student_id", sa.String(length=64), nullable=False),
        sa.PrimaryKeyConstraint("event_id"),
    )
    op.create_index(
        "ix_processed_access_events_course_id",
        "processed_access_events",
        ["course_id"],
        unique=False,
    )
    op.create_index(
        "ix_processed_access_events_student_id",
        "processed_access_events",
        ["student_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_processed_access_events_student_id",
        table_name="processed_access_events",
    )
    op.drop_index(
        "ix_processed_access_events_course_id",
        table_name="processed_access_events",
    )
    op.drop_table("processed_access_events")
