"""intervention_decisions

Revision ID: f1a2b3c4d5e6
Revises: 78dc1fecb74e
Create Date: 2026-07-11 12:45:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'f1a2b3c4d5e6'
down_revision: Union[str, None] = '78dc1fecb74e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('intervention_decisions',
    sa.Column('id', sa.String(length=255), nullable=False),
    sa.Column('session_id', sa.String(length=255), nullable=False),
    sa.Column('user_id', sa.String(length=255), nullable=False),
    sa.Column('lab_slug', sa.String(length=255), nullable=False),
    sa.Column('spell_id', sa.String(length=255), nullable=False),
    sa.Column('ts', sa.DateTime(timezone=True), nullable=False),
    sa.Column('regime', sa.String(length=50), nullable=False),
    sa.Column('dwell_seconds', sa.Float(), nullable=False),
    sa.Column('t_k_applied', sa.Float(), nullable=False),
    sa.Column('assignment', sa.String(length=20), nullable=False),
    sa.Column('subsequent_exit_ts', sa.DateTime(timezone=True), nullable=True),
    sa.Column('censored', sa.Boolean(), nullable=False, server_default=sa.false()),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['session_id'], ['learning_sessions.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_intervention_decisions_session_ts', 'intervention_decisions', ['session_id', 'ts'], unique=False)
    op.create_index('ix_intervention_decisions_spell', 'intervention_decisions', ['spell_id'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_intervention_decisions_spell', table_name='intervention_decisions')
    op.drop_index('ix_intervention_decisions_session_ts', table_name='intervention_decisions')
    op.drop_table('intervention_decisions')
