"""add learning_session model_id

Revision ID: 9412b171345d
Revises: 4567567ebcc6
Create Date: 2026-06-17 09:17:51.291931
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '9412b171345d'
down_revision: Union[str, None] = '4567567ebcc6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("learning_sessions", sa.Column("model_id", sa.String(length=255), nullable=True))


def downgrade() -> None:
    op.drop_column("learning_sessions", "model_id")
