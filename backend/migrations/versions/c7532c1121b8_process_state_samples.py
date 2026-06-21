"""process_state_samples

Revision ID: c7532c1121b8
Revises: 8d7005789325
Create Date: 2026-06-21 01:00:53.517501
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'c7532c1121b8'
down_revision: Union[str, None] = '8d7005789325'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('process_state_samples',
    sa.Column('id', sa.String(length=255), nullable=False),
    sa.Column('session_id', sa.String(length=255), nullable=False),
    sa.Column('user_id', sa.String(length=255), nullable=False),
    sa.Column('lab_slug', sa.String(length=255), nullable=False),
    sa.Column('ts', sa.DateTime(timezone=True), nullable=False),
    sa.Column('regime', sa.String(length=50), nullable=False),
    sa.Column('dwell_seconds', sa.Float(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['session_id'], ['learning_sessions.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_process_state_samples_session_ts', 'process_state_samples', ['session_id', 'ts'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_process_state_samples_session_ts', table_name='process_state_samples')
    op.drop_table('process_state_samples')
