"""create course catalog table

Revision ID: 20260412_0002
Revises: 20260406_0001
Create Date: 2026-04-12
"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20260412_0002"
down_revision: Union[str, Sequence[str], None] = "20260406_0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "course_catalog",
        sa.Column("course_id", sa.String(length=36), primary_key=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("teacher_id", sa.String(length=64), nullable=False),
        sa.Column("teacher_display_name", sa.String(length=255), nullable=True),
        sa.Column("slug", sa.String(length=255), nullable=False),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("duration_days", sa.Integer(), nullable=False),
        sa.Column("access_ttl_days", sa.Integer(), nullable=True),
        sa.Column("enrollment_opens_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("enrollment_closes_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("timezone", sa.String(length=64), nullable=False),
        sa.Column("price", sa.Numeric(12, 2), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("language", sa.String(length=16), nullable=False),
        sa.Column("age_min", sa.Integer(), nullable=True),
        sa.Column("age_max", sa.Integer(), nullable=True),
        sa.Column("level", sa.String(length=32), nullable=False),
        sa.Column("max_students", sa.Integer(), nullable=True),
        sa.Column("tags", sa.JSON(), nullable=False),
        sa.Column("cover_image_url", sa.Text(), nullable=True),
        sa.Column("is_live_enabled", sa.Boolean(), nullable=False),
        sa.Column("live_room_template_id", sa.String(length=64), nullable=True),
        sa.Column("publish_state", sa.String(length=32), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("published_by_admin_id", sa.String(length=64), nullable=True),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("archived_by", sa.String(length=64), nullable=True),
        sa.Column("seo_meta_title", sa.String(length=70), nullable=False),
        sa.Column("seo_meta_description", sa.String(length=160), nullable=False),
        sa.Column("seo_canonical_url", sa.Text(), nullable=True),
        sa.Column("seo_robots", sa.String(length=16), nullable=False),
        sa.Column("seo_og_image_url", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_by", sa.String(length=64), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_by", sa.String(length=64), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.UniqueConstraint("slug", name="uq_course_catalog_slug"),
    )
    op.create_index(
        "ix_course_catalog_teacher_id", "course_catalog", ["teacher_id"], unique=False
    )
    op.create_index("ix_course_catalog_slug", "course_catalog", ["slug"], unique=False)
    op.create_index(
        "ix_course_catalog_starts_at", "course_catalog", ["starts_at"], unique=False
    )
    op.create_index(
        "ix_course_catalog_publish_state",
        "course_catalog",
        ["publish_state"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_course_catalog_publish_state", table_name="course_catalog")
    op.drop_index("ix_course_catalog_starts_at", table_name="course_catalog")
    op.drop_index("ix_course_catalog_slug", table_name="course_catalog")
    op.drop_index("ix_course_catalog_teacher_id", table_name="course_catalog")
    op.drop_table("course_catalog")
