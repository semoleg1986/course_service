"""create access projection tables

Revision ID: 20260406_0001
Revises: 
Create Date: 2026-04-06
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "20260406_0001"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "course_owner_projections",
        sa.Column("course_id", sa.String(length=36), primary_key=True),
        sa.Column("owner_account_id", sa.String(length=64), nullable=False),
    )
    op.create_index(
        "ix_course_owner_projections_owner_account_id",
        "course_owner_projections",
        ["owner_account_id"],
        unique=False,
    )

    op.create_table(
        "access_grant_projections",
        sa.Column("course_id", sa.String(length=36), nullable=False),
        sa.Column("student_id", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.PrimaryKeyConstraint("course_id", "student_id"),
    )
    op.create_index(
        "ix_access_grant_projections_course_id",
        "access_grant_projections",
        ["course_id"],
        unique=False,
    )
    op.create_index(
        "ix_access_grant_projections_student_id",
        "access_grant_projections",
        ["student_id"],
        unique=False,
    )
    op.create_index(
        "ix_access_grant_projections_status",
        "access_grant_projections",
        ["status"],
        unique=False,
    )

    op.create_table(
        "enrollment_projections",
        sa.Column("course_id", sa.String(length=36), nullable=False),
        sa.Column("student_id", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.PrimaryKeyConstraint("course_id", "student_id"),
    )
    op.create_index(
        "ix_enrollment_projections_course_id",
        "enrollment_projections",
        ["course_id"],
        unique=False,
    )
    op.create_index(
        "ix_enrollment_projections_student_id",
        "enrollment_projections",
        ["student_id"],
        unique=False,
    )
    op.create_index(
        "ix_enrollment_projections_status",
        "enrollment_projections",
        ["status"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_enrollment_projections_status", table_name="enrollment_projections")
    op.drop_index("ix_enrollment_projections_student_id", table_name="enrollment_projections")
    op.drop_index("ix_enrollment_projections_course_id", table_name="enrollment_projections")
    op.drop_table("enrollment_projections")

    op.drop_index("ix_access_grant_projections_status", table_name="access_grant_projections")
    op.drop_index("ix_access_grant_projections_student_id", table_name="access_grant_projections")
    op.drop_index("ix_access_grant_projections_course_id", table_name="access_grant_projections")
    op.drop_table("access_grant_projections")

    op.drop_index(
        "ix_course_owner_projections_owner_account_id",
        table_name="course_owner_projections",
    )
    op.drop_table("course_owner_projections")
