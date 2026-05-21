"""add learning_sessions user indexes

Revision ID: b6b768a5bd77
Revises: 41942c30dead
Create Date: 2026-05-31 16:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'b6b768a5bd77'
down_revision: Union[str, None] = '41942c30dead'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index(
        "ix_learning_sessions_user_status",
        "learning_sessions",
        ["user_id", "status"],
    )
    op.create_index(
        "ix_learning_sessions_user_started",
        "learning_sessions",
        ["user_id", "started_at"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_learning_sessions_user_started", table_name="learning_sessions"
    )
    op.drop_index(
        "ix_learning_sessions_user_status", table_name="learning_sessions"
    )
