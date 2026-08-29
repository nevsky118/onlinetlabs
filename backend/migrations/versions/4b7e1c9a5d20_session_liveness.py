"""session liveness: last_seen_at, paused_at, expires_at

Revision ID: 4b7e1c9a5d20
Revises: 9c1f4a7d2b30
Create Date: 2026-08-29 10:00:00.000000
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = '4b7e1c9a5d20'
down_revision: Union[str, None] = '9c1f4a7d2b30'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# matches progress_max_duration_hours default
_DEFAULT_MAX_DURATION_HOURS = 12


def upgrade() -> None:
    op.add_column(
        'learning_sessions',
        sa.Column('last_seen_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        'learning_sessions',
        sa.Column('paused_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        'learning_sessions',
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
    )
    # backfill before NOT NULL
    op.execute("UPDATE learning_sessions SET last_seen_at = started_at")
    op.alter_column('learning_sessions', 'last_seen_at', nullable=False)
    # otherwise old sessions never expire
    op.execute(
        "UPDATE learning_sessions "
        f"SET expires_at = started_at + interval '{_DEFAULT_MAX_DURATION_HOURS} hours' "
        "WHERE status IN ('active', 'provisioning')"
    )
    op.create_index(
        'ix_learning_sessions_status_last_seen', 'learning_sessions', ['status', 'last_seen_at']
    )
    op.create_index(
        'ix_learning_sessions_status_expires', 'learning_sessions', ['status', 'expires_at']
    )


def downgrade() -> None:
    op.drop_index('ix_learning_sessions_status_expires', table_name='learning_sessions')
    op.drop_index('ix_learning_sessions_status_last_seen', table_name='learning_sessions')
    op.drop_column('learning_sessions', 'expires_at')
    op.drop_column('learning_sessions', 'paused_at')
    op.drop_column('learning_sessions', 'last_seen_at')
