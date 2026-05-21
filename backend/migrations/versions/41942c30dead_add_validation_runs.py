"""add validation_runs

Revision ID: 41942c30dead
Revises: 8f3899096077
Create Date: 2026-05-31 15:30:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB


revision: str = '41942c30dead'
down_revision: Union[str, None] = '8f3899096077'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'validation_runs',
        sa.Column('id', sa.String(length=255), nullable=False),
        sa.Column('session_id', sa.String(length=255), nullable=False),
        sa.Column('lab_slug', sa.String(length=255), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column(
            'steps',
            JSONB(),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column(
            'started_at',
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text('now()'),
        ),
        sa.Column('finished_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ['session_id'], ['learning_sessions.id'], ondelete='CASCADE'
        ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(
        'validation_runs_session_idx',
        'validation_runs',
        ['session_id', sa.text('started_at DESC')],
    )


def downgrade() -> None:
    op.drop_index('validation_runs_session_idx', table_name='validation_runs')
    op.drop_table('validation_runs')
