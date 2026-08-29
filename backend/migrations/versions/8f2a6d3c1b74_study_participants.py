"""study_participants: the pseudonym to account-identity link table

Revision ID: 8f2a6d3c1b74
Revises: 4b7e1c9a5d20
Create Date: 2026-08-29 10:05:00.000000
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = '8f2a6d3c1b74'
down_revision: Union[str, None] = '4b7e1c9a5d20'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'study_participants',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=255), nullable=False),
        sa.Column('pseudonym', sa.String(length=36), nullable=False),
        sa.Column(
            'enrolled_at',
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text('now()'),
        ),
        sa.Column('withdrawn_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id'),
        sa.UniqueConstraint('pseudonym'),
    )
    op.create_index('ix_study_participants_pseudonym', 'study_participants', ['pseudonym'])
    # backfill: every account needs a pseudonym
    op.execute(
        "CREATE EXTENSION IF NOT EXISTS pgcrypto"
    )
    op.execute(
        "INSERT INTO study_participants (id, user_id, pseudonym, enrolled_at) "
        "SELECT gen_random_uuid()::text, id, gen_random_uuid()::text, now() FROM users"
    )


def downgrade() -> None:
    op.drop_index('ix_study_participants_pseudonym', table_name='study_participants')
    op.drop_table('study_participants')
