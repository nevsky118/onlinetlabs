"""add learning_sessions indexes

Revision ID: ae6f7575c5cc
Revises: cf531c4ea7fc
Create Date: 2026-05-31 14:22:11.243270
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'ae6f7575c5cc'
down_revision: Union[str, None] = 'cf531c4ea7fc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index(
        "ix_learning_sessions_user_lab_status",
        "learning_sessions",
        ["user_id", "lab_slug", "status"],
    )
    op.create_index(
        "ix_learning_sessions_user_id",
        "learning_sessions",
        ["user_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_learning_sessions_user_id", table_name="learning_sessions")
    op.drop_index("ix_learning_sessions_user_lab_status", table_name="learning_sessions")
