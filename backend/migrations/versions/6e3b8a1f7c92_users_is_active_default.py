"""users.is_active: drop the server default that contradicted the ORM default

Revision ID: 6e3b8a1f7c92
Revises: 1d9c4e8b2a56
Create Date: 2026-08-29 10:15:00.000000
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = '6e3b8a1f7c92'
down_revision: Union[str, None] = '1d9c4e8b2a56'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # server_default 'true' contradicted the ORM default False
    op.alter_column('users', 'is_active', server_default=None)


def downgrade() -> None:
    op.alter_column('users', 'is_active', server_default=sa.text('true'))
