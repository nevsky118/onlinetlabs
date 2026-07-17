"""cycle_latency_samples

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-07-11 13:45:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'c3d4e5f6a7b8'
down_revision: Union[str, None] = 'b2c3d4e5f6a7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('cycle_latency_samples',
    sa.Column('id', sa.String(length=255), nullable=False),
    sa.Column('session_id', sa.String(length=255), nullable=False),
    sa.Column('stage', sa.String(length=50), nullable=False),
    sa.Column('duration_ms', sa.Float(), nullable=False),
    sa.Column('ts', sa.DateTime(timezone=True), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['session_id'], ['learning_sessions.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_cycle_latency_samples_session_stage', 'cycle_latency_samples', ['session_id', 'stage'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_cycle_latency_samples_session_stage', table_name='cycle_latency_samples')
    op.drop_table('cycle_latency_samples')
