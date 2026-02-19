"""add courses, labs, progress, sessions

Revision ID: 002
Revises: a71aa2584864
Create Date: 2026-03-01
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "002"
down_revision: Union[str, None] = "a71aa2584864"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "courses",
        sa.Column("slug", sa.String(255), primary_key=True),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "difficulty", sa.String(50), server_default="beginner", nullable=False
        ),
        sa.Column("order", sa.Integer(), server_default="0", nullable=False),
        sa.Column("prerequisites", sa.JSON(), nullable=True),
        sa.Column("meta", sa.JSON(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    op.create_table(
        "labs",
        sa.Column("slug", sa.String(255), primary_key=True),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "difficulty", sa.String(50), server_default="beginner", nullable=False
        ),
        sa.Column(
            "course_slug",
            sa.String(255),
            sa.ForeignKey("courses.slug", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("order_in_course", sa.Integer(), server_default="0", nullable=False),
        sa.Column(
            "environment_type", sa.String(50), server_default="none", nullable=False
        ),
        sa.Column("meta", sa.JSON(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    op.create_table(
        "lab_steps",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "lab_slug",
            sa.String(255),
            sa.ForeignKey("labs.slug", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("step_order", sa.Integer(), nullable=False),
        sa.Column("slug", sa.String(255), nullable=False),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("validation_type", sa.String(100), nullable=True),
    )

    op.create_table(
        "course_progress",
        sa.Column("id", sa.String(255), primary_key=True),
        sa.Column(
            "user_id",
            sa.String(255),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "course_slug",
            sa.String(255),
            sa.ForeignKey("courses.slug", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "status", sa.String(50), server_default="not_started", nullable=False
        ),
        sa.Column("score", sa.Float(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint(
            "user_id", "course_slug", name="uq_course_progress_user_course"
        ),
    )

    op.create_table(
        "lab_progress",
        sa.Column("id", sa.String(255), primary_key=True),
        sa.Column(
            "user_id",
            sa.String(255),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "lab_slug",
            sa.String(255),
            sa.ForeignKey("labs.slug", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "status", sa.String(50), server_default="not_started", nullable=False
        ),
        sa.Column("score", sa.Float(), nullable=True),
        sa.Column("current_step", sa.Integer(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint("user_id", "lab_slug", name="uq_lab_progress_user_lab"),
    )

    op.create_table(
        "step_attempts",
        sa.Column("id", sa.String(255), primary_key=True),
        sa.Column(
            "user_id",
            sa.String(255),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "lab_slug",
            sa.String(255),
            sa.ForeignKey("labs.slug", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("step_slug", sa.String(255), nullable=False),
        sa.Column("attempt_number", sa.Integer(), nullable=False),
        sa.Column("result", sa.String(50), nullable=False),
        sa.Column("score", sa.Float(), nullable=True),
        sa.Column("error_details", sa.JSON(), nullable=True),
        sa.Column(
            "started_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.create_table(
        "learning_sessions",
        sa.Column("id", sa.String(255), primary_key=True),
        sa.Column(
            "user_id",
            sa.String(255),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "lab_slug",
            sa.String(255),
            sa.ForeignKey("labs.slug", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("status", sa.String(50), server_default="active", nullable=False),
        sa.Column(
            "started_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("meta", sa.JSON(), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("learning_sessions")
    op.drop_table("step_attempts")
    op.drop_table("lab_progress")
    op.drop_table("course_progress")
    op.drop_table("lab_steps")
    op.drop_table("labs")
    op.drop_table("courses")
