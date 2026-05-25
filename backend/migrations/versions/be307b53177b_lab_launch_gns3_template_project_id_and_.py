"""lab_launch gns3_template_project_id and chat_messages

Revision ID: be307b53177b
Revises: 003
Create Date: 2026-05-28 13:57:43.724167
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = 'be307b53177b'
down_revision: Union[str, None] = '003'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('chat_messages',
    sa.Column('id', sa.String(length=255), nullable=False),
    sa.Column('session_id', sa.String(length=255), nullable=False),
    sa.Column('role', sa.String(length=20), nullable=False),
    sa.Column('parts', postgresql.JSON(astext_type=sa.Text()), nullable=False),
    sa.Column('usage', postgresql.JSON(astext_type=sa.Text()), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['session_id'], ['learning_sessions.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_chat_messages_session_id'), 'chat_messages', ['session_id'], unique=False)
    op.add_column('labs', sa.Column('gns3_template_project_id', sa.String(length=255), nullable=True))


def downgrade() -> None:
    op.drop_column('labs', 'gns3_template_project_id')
    op.drop_index(op.f('ix_chat_messages_session_id'), table_name='chat_messages')
    op.drop_table('chat_messages')
