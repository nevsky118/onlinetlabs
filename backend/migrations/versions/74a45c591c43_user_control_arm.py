"""user_control_arm

Revision ID: 74a45c591c43
Revises: c7532c1121b8
Create Date: 2026-06-21 12:58:35.117577
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '74a45c591c43'
down_revision: Union[str, None] = 'c7532c1121b8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("control_arm", sa.String(20), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "control_arm")
