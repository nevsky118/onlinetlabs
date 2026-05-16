"""Метаданные эксперимента OpenClaw

Revision ID: 003
Revises: 002
Дата создания: 2026-05-16
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = set(inspector.get_table_names())

    if "users" in tables:
        user_columns = {column["name"] for column in inspector.get_columns("users")}
        if "experiment_group" not in user_columns:
            op.add_column(
                "users",
                sa.Column("experiment_group", sa.String(length=20), nullable=True),
            )

    if "experiment_metrics" not in tables:
        op.create_table(
            "experiment_metrics",
            sa.Column("id", sa.String(length=255), primary_key=True),
            sa.Column(
                "session_id",
                sa.String(length=255),
                sa.ForeignKey("learning_sessions.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column(
                "user_id",
                sa.String(length=255),
                sa.ForeignKey("users.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column("lab_slug", sa.String(length=255), nullable=False),
            sa.Column("experiment_group", sa.String(length=20), nullable=False),
            sa.Column("agent_backend", sa.String(length=50), nullable=True),
            sa.Column("total_time_seconds", sa.Float(), nullable=False),
            sa.Column("steps_completed", sa.Integer(), nullable=False),
            sa.Column("total_errors", sa.Integer(), nullable=False),
            sa.Column("repeated_errors", sa.Integer(), nullable=False),
            sa.Column("unique_error_types", sa.Integer(), nullable=False),
            sa.Column(
                "interventions_received",
                sa.Integer(),
                server_default="0",
                nullable=False,
            ),
            sa.Column(
                "interventions_succeeded",
                sa.Integer(),
                server_default="0",
                nullable=False,
            ),
            sa.Column(
                "interventions_failed", sa.Integer(), server_default="0", nullable=False
            ),
            sa.Column(
                "interventions_accepted",
                sa.Integer(),
                server_default="0",
                nullable=False,
            ),
            sa.Column("final_score", sa.Float(), nullable=False),
            sa.Column(
                "completed", sa.Boolean(), server_default=sa.false(), nullable=False
            ),
            sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.func.now(),
                nullable=False,
            ),
        )
        return

    columns = {column["name"] for column in inspector.get_columns("experiment_metrics")}
    if "agent_backend" not in columns:
        op.add_column(
            "experiment_metrics",
            sa.Column("agent_backend", sa.String(length=50), nullable=True),
        )
    if "interventions_succeeded" not in columns:
        op.add_column(
            "experiment_metrics",
            sa.Column(
                "interventions_succeeded",
                sa.Integer(),
                server_default="0",
                nullable=False,
            ),
        )
    if "interventions_failed" not in columns:
        op.add_column(
            "experiment_metrics",
            sa.Column(
                "interventions_failed", sa.Integer(), server_default="0", nullable=False
            ),
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = set(inspector.get_table_names())
    if "experiment_metrics" in tables:
        columns = {
            column["name"] for column in inspector.get_columns("experiment_metrics")
        }
        if "interventions_failed" in columns:
            op.drop_column("experiment_metrics", "interventions_failed")
        if "interventions_succeeded" in columns:
            op.drop_column("experiment_metrics", "interventions_succeeded")
        if "agent_backend" in columns:
            op.drop_column("experiment_metrics", "agent_backend")
    if "users" in tables:
        user_columns = {column["name"] for column in inspector.get_columns("users")}
        if "experiment_group" in user_columns:
            op.drop_column("users", "experiment_group")
