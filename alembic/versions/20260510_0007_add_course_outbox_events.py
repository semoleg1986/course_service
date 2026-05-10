"""add course outbox events

Revision ID: 20260510_0007
Revises: 20260502_0006
Create Date: 2026-05-10
"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

revision: str = "20260510_0007"
down_revision: Union[str, Sequence[str], None] = "20260502_0006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "course_outbox_events",
        sa.Column("event_id", sa.String(length=64), nullable=False),
        sa.Column("aggregate_type", sa.String(length=64), nullable=False),
        sa.Column("aggregate_id", sa.String(length=128), nullable=False),
        sa.Column("event_type", sa.String(length=64), nullable=False),
        sa.Column("payload_json", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("attempt_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("available_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("event_id"),
        sa.UniqueConstraint(
            "aggregate_type",
            "aggregate_id",
            "event_type",
            name="uq_course_outbox_aggregate_event_type",
        ),
    )
    op.create_index(
        "ix_course_outbox_events_aggregate_type",
        "course_outbox_events",
        ["aggregate_type"],
        unique=False,
    )
    op.create_index(
        "ix_course_outbox_events_aggregate_id",
        "course_outbox_events",
        ["aggregate_id"],
        unique=False,
    )
    op.create_index(
        "ix_course_outbox_events_event_type",
        "course_outbox_events",
        ["event_type"],
        unique=False,
    )
    op.create_index(
        "ix_course_outbox_events_status",
        "course_outbox_events",
        ["status"],
        unique=False,
    )
    op.create_index(
        "ix_course_outbox_events_available_at",
        "course_outbox_events",
        ["available_at"],
        unique=False,
    )
    op.create_index(
        "ix_course_outbox_events_created_at",
        "course_outbox_events",
        ["created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_course_outbox_events_created_at", table_name="course_outbox_events"
    )
    op.drop_index(
        "ix_course_outbox_events_available_at", table_name="course_outbox_events"
    )
    op.drop_index("ix_course_outbox_events_status", table_name="course_outbox_events")
    op.drop_index(
        "ix_course_outbox_events_event_type", table_name="course_outbox_events"
    )
    op.drop_index(
        "ix_course_outbox_events_aggregate_id", table_name="course_outbox_events"
    )
    op.drop_index(
        "ix_course_outbox_events_aggregate_type", table_name="course_outbox_events"
    )
    op.drop_table("course_outbox_events")
