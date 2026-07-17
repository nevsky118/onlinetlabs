"""grounding_comparisons

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-07-11 13:58:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'd4e5f6a7b8c9'
down_revision: Union[str, None] = 'c3d4e5f6a7b8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('grounding_comparisons',
    sa.Column('id', sa.String(length=255), nullable=False),
    sa.Column('session_id', sa.String(length=255), nullable=False),
    sa.Column('grounded_text', sa.Text(), nullable=False),
    sa.Column('ungrounded_text', sa.Text(), nullable=False),
    sa.Column('ts', sa.DateTime(timezone=True), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['session_id'], ['learning_sessions.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_grounding_comparisons_session', 'grounding_comparisons', ['session_id'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_grounding_comparisons_session', table_name='grounding_comparisons')
    op.drop_table('grounding_comparisons')
