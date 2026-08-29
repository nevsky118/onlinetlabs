"""learning_sessions.research_id: opaque session key for research exports

Revision ID: 7c4d2e9a6b18
Revises: 2a5f9d4c8e13
Create Date: 2026-08-29 12:00:00.000000
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = '7c4d2e9a6b18'
down_revision: Union[str, None] = '2a5f9d4c8e13'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'learning_sessions',
        sa.Column('research_id', sa.String(length=36), nullable=True),
    )
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")
    # random, not derived: a hash of the session id is reversible by anyone holding it
    op.execute("UPDATE learning_sessions SET research_id = gen_random_uuid()::text")
    op.alter_column('learning_sessions', 'research_id', nullable=False)
    op.create_unique_constraint(
        'uq_learning_sessions_research_id', 'learning_sessions', ['research_id']
    )


def downgrade() -> None:
    op.drop_constraint(
        'uq_learning_sessions_research_id', 'learning_sessions', type_='unique'
    )
    op.drop_column('learning_sessions', 'research_id')
