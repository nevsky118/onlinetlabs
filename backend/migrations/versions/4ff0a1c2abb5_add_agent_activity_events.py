"""add agent_activity_events

Revision ID: 4ff0a1c2abb5
Revises: 9412b171345d
Create Date: 2026-06-18 17:20:07.374214
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = '4ff0a1c2abb5'
down_revision: Union[str, None] = '9412b171345d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'agent_activity_events',
        sa.Column('id', sa.String(length=255), nullable=False),
        sa.Column('session_id', sa.String(length=255), nullable=False),
        sa.Column('user_id', sa.String(length=255), nullable=False),
        sa.Column('ts', sa.DateTime(timezone=True), nullable=False),
        sa.Column('source', sa.String(length=20), nullable=False),
        sa.Column('kind', sa.String(length=40), nullable=False),
        sa.Column('agent', sa.String(length=40), nullable=True),
        sa.Column('severity', sa.String(length=10), nullable=False),
        sa.Column('summary', sa.Text(), nullable=False),
        sa.Column('detail', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_agent_activity_session_ts', 'agent_activity_events', ['session_id', 'ts'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_agent_activity_session_ts', table_name='agent_activity_events')
    op.drop_table('agent_activity_events')
