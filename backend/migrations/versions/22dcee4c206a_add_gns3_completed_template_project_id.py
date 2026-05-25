"""add gns3_completed_template_project_id

Revision ID: 22dcee4c206a
Revises: e37ebf363a30
Create Date: 2026-05-31 11:15:37.997155
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '22dcee4c206a'
down_revision: Union[str, None] = 'e37ebf363a30'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('labs', sa.Column('gns3_completed_template_project_id', sa.String(length=255), nullable=True))


def downgrade() -> None:
    op.drop_column('labs', 'gns3_completed_template_project_id')
