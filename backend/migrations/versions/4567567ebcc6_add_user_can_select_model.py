"""add user can_select_model

Revision ID: 4567567ebcc6
Revises: 628ccc7b885a
Create Date: 2026-06-17 09:14:30.769893
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '4567567ebcc6'
down_revision: Union[str, None] = '628ccc7b885a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("can_select_model", sa.Boolean(), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "can_select_model")
