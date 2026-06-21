"""experiment_metrics: control_arm, escalations, would_interventions, l1_interventions, l2_unassisted_pass

Revision ID: 004_experiment_metrics_ab_task8
Revises: 003
Create Date: 2026-06-21
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "004_experiment_metrics_ab_task8"
down_revision: Union[str, None] = "74a45c591c43"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = set(inspector.get_table_names())
    if "experiment_metrics" not in tables:
        return
    columns = {col["name"] for col in inspector.get_columns("experiment_metrics")}
    if "control_arm" not in columns:
        op.add_column(
            "experiment_metrics",
            sa.Column("control_arm", sa.String(20), nullable=True),
        )
    if "escalations" not in columns:
        op.add_column(
            "experiment_metrics",
            sa.Column("escalations", sa.Integer(), server_default="0", nullable=False),
        )
    if "would_interventions" not in columns:
        op.add_column(
            "experiment_metrics",
            sa.Column("would_interventions", sa.Integer(), server_default="0", nullable=False),
        )
    if "l1_interventions" not in columns:
        op.add_column(
            "experiment_metrics",
            sa.Column("l1_interventions", sa.Integer(), server_default="0", nullable=False),
        )
    if "l2_unassisted_pass" not in columns:
        op.add_column(
            "experiment_metrics",
            sa.Column("l2_unassisted_pass", sa.Boolean(), nullable=True),
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = set(inspector.get_table_names())
    if "experiment_metrics" not in tables:
        return
    columns = {col["name"] for col in inspector.get_columns("experiment_metrics")}
    for col in ("l2_unassisted_pass", "l1_interventions", "would_interventions", "escalations", "control_arm"):
        if col in columns:
            op.drop_column("experiment_metrics", col)
