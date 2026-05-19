"""platform_events

Revision ID: 628ccc7b885a
Revises: b6b768a5bd77
Create Date: 2026-06-01 14:32:27.839328
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '628ccc7b885a'
down_revision: Union[str, None] = 'b6b768a5bd77'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'platform_events',
        sa.Column('id', sa.String(length=255), nullable=False),
        sa.Column('event_name', sa.String(length=100), nullable=False),
        sa.Column('user_id', sa.String(length=255), nullable=True),
        sa.Column('session_id', sa.String(length=255), nullable=True),
        sa.Column('device_id', sa.String(length=100), nullable=False),
        sa.Column(
            'properties',
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'"),
            nullable=False,
        ),
        sa.Column('client_ts', sa.DateTime(timezone=True), nullable=False),
        sa.Column('server_ts', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['session_id'], ['learning_sessions.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_platform_events_device_ts', 'platform_events', ['device_id', 'server_ts'], unique=False)
    op.create_index('ix_platform_events_name_ts', 'platform_events', ['event_name', 'server_ts'], unique=False)
    op.create_index('ix_platform_events_session', 'platform_events', ['session_id'], unique=False)
    op.create_index('ix_platform_events_user_ts', 'platform_events', ['user_id', 'server_ts'], unique=False)
    # Вспомогательное представление поднимает частые измерения из общего
    # JSONB наружу как колонки, чтобы ручной SQL для исследования был удобнее
    op.execute(
        sa.text(
            """
            CREATE VIEW platform_events_flat AS
            SELECT
                id, event_name, user_id, session_id, device_id,
                properties,
                properties->>'lab_slug'   AS lab_slug,
                properties->>'page'       AS page,
                properties->>'user_agent' AS user_agent,
                client_ts, server_ts
            FROM platform_events
            """
        )
    )


def downgrade() -> None:
    op.execute(sa.text("DROP VIEW IF EXISTS platform_events_flat"))
    op.drop_index('ix_platform_events_user_ts', table_name='platform_events')
    op.drop_index('ix_platform_events_session', table_name='platform_events')
    op.drop_index('ix_platform_events_name_ts', table_name='platform_events')
    op.drop_index('ix_platform_events_device_ts', table_name='platform_events')
    op.drop_table('platform_events')
