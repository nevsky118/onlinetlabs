"""add gns3_template_project_id_frr

Revision ID: 8f3899096077
Revises: ae6f7575c5cc
Create Date: 2026-05-31 15:01:16.486617
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '8f3899096077'
down_revision: Union[str, None] = 'ae6f7575c5cc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('labs', sa.Column('gns3_template_project_id_frr', sa.String(length=255), nullable=True))


def downgrade() -> None:
    op.drop_column('labs', 'gns3_template_project_id_frr')
