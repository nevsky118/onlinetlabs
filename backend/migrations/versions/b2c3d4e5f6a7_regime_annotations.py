"""regime_annotations

Revision ID: b2c3d4e5f6a7
Revises: a7b8c9d0e1f2
Create Date: 2026-07-11 13:20:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'b2c3d4e5f6a7'
down_revision: Union[str, None] = 'a7b8c9d0e1f2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('regime_annotations',
    sa.Column('id', sa.String(length=255), nullable=False),
    sa.Column('session_id', sa.String(length=255), nullable=False),
    sa.Column('coder_id', sa.String(length=255), nullable=False),
    sa.Column('window_index', sa.Integer(), nullable=False),
    sa.Column('regime_label', sa.String(length=50), nullable=False),
    sa.Column('is_gold', sa.Boolean(), nullable=False, server_default=sa.false()),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['session_id'], ['learning_sessions.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_regime_annotations_session_window', 'regime_annotations', ['session_id', 'window_index'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_regime_annotations_session_window', table_name='regime_annotations')
    op.drop_table('regime_annotations')
