"""add user can_view_agent_logs

Revision ID: 8d7005789325
Revises: 4ff0a1c2abb5
Create Date: 2026-06-18 17:28:18.806316
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '8d7005789325'
down_revision: Union[str, None] = '4ff0a1c2abb5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("can_view_agent_logs", sa.Boolean(), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "can_view_agent_logs")
