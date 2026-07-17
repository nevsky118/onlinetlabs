"""drop redundant ix_learning_sessions_user_id

Revision ID: 28f5bc28a3c2
Revises: e5f6a7b8c9d0
Create Date: 2026-07-17 12:00:00.000000
"""
from typing import Sequence, Union

from alembic import op


revision: str = '28f5bc28a3c2'
down_revision: Union[str, None] = 'e5f6a7b8c9d0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ix_learning_sessions_user_lab_status / user_status / user_started already
    # lead with user_id — this single-column index is a redundant subset.
    op.drop_index("ix_learning_sessions_user_id", table_name="learning_sessions")


def downgrade() -> None:
    op.create_index("ix_learning_sessions_user_id", "learning_sessions", ["user_id"])
