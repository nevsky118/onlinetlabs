"""consents: decision and policy_version

Revision ID: 1d9c4e8b2a56
Revises: 8f2a6d3c1b74
Create Date: 2026-08-29 10:10:00.000000
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = '1d9c4e8b2a56'
down_revision: Union[str, None] = '8f2a6d3c1b74'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# wording shipped before this migration
_LEGACY_POLICY_VERSION = '0'


def upgrade() -> None:
    op.add_column(
        'consents',
        sa.Column('decision', sa.String(length=20), nullable=False, server_default='granted'),
    )
    op.add_column(
        'consents',
        sa.Column(
            'policy_version',
            sa.String(length=20),
            nullable=False,
            server_default=_LEGACY_POLICY_VERSION,
        ),
    )
    op.create_index('ix_consents_user_scope', 'consents', ['user_id', 'scope'])
    op.alter_column('consents', 'decision', server_default=None)


def downgrade() -> None:
    op.drop_index('ix_consents_user_scope', table_name='consents')
    op.drop_column('consents', 'policy_version')
    op.drop_column('consents', 'decision')
