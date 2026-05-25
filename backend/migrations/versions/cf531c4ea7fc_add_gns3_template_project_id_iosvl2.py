"""add gns3_template_project_id_iosvl2

Revision ID: cf531c4ea7fc
Revises: 22dcee4c206a
Create Date: 2026-05-31 12:10:08.111386
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'cf531c4ea7fc'
down_revision: Union[str, None] = '22dcee4c206a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('labs', sa.Column('gns3_template_project_id_iosvl2', sa.String(length=255), nullable=True))


def downgrade() -> None:
    op.drop_column('labs', 'gns3_template_project_id_iosvl2')
