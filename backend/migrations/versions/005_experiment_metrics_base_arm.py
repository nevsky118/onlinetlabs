"""experiment_metrics: добавлена колонка base_arm (постоянный training-arm пользователя)

Revision ID: 005_experiment_metrics_base_arm
Revises: 004_experiment_metrics_ab_task8
Create Date: 2026-06-21
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "005_experiment_metrics_base_arm"
down_revision: Union[str, None] = "004_experiment_metrics_ab_task8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = set(inspector.get_table_names())
    if "experiment_metrics" not in tables:
        return
    columns = {col["name"] for col in inspector.get_columns("experiment_metrics")}
    if "base_arm" not in columns:
        op.add_column(
            "experiment_metrics",
            sa.Column("base_arm", sa.String(20), nullable=True),
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = set(inspector.get_table_names())
    if "experiment_metrics" not in tables:
        return
    columns = {col["name"] for col in inspector.get_columns("experiment_metrics")}
    if "base_arm" in columns:
        op.drop_column("experiment_metrics", "base_arm")
