"""i18n: session locale and localized lab/course content

Revision ID: 9c1f4a7d2b30
Revises: 28f5bc28a3c2
Create Date: 2026-08-02 12:00:00.000000
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = '9c1f4a7d2b30'
down_revision: Union[str, None] = '28f5bc28a3c2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_CONTENT_TABLES = ('labs', 'courses')


def upgrade() -> None:
    op.add_column(
        'learning_sessions',
        sa.Column('locale', sa.String(length=5), nullable=False, server_default='en'),
    )
    for table in _CONTENT_TABLES:
        op.add_column(table, sa.Column('title_i18n', postgresql.JSONB(), nullable=True))
        op.add_column(table, sa.Column('description_i18n', postgresql.JSONB(), nullable=True))
        op.execute(f"UPDATE {table} SET title_i18n = jsonb_build_object('en', title)")
        op.execute(
            f"UPDATE {table} SET description_i18n = jsonb_build_object('en', description) "
            f"WHERE description IS NOT NULL"
        )
        op.alter_column(table, 'title_i18n', nullable=False)
        op.drop_column(table, 'title')
        op.drop_column(table, 'description')


def downgrade() -> None:
    for table in _CONTENT_TABLES:
        op.add_column(table, sa.Column('title', sa.String(length=500), nullable=True))
        op.add_column(table, sa.Column('description', sa.Text(), nullable=True))
        # Mirror resolve_localized's chain: en, then any present value, then the slug.
        op.execute(
            f"UPDATE {table} SET title = COALESCE("
            f"title_i18n ->> 'en', "
            f"(SELECT value FROM jsonb_each_text(title_i18n) LIMIT 1), "
            f"slug)"
        )
        op.execute(
            f"UPDATE {table} SET description = COALESCE("
            f"description_i18n ->> 'en', "
            f"(SELECT value FROM jsonb_each_text(description_i18n) LIMIT 1))"
            f" WHERE description_i18n IS NOT NULL"
        )
        op.alter_column(table, 'title', nullable=False)
        op.drop_column(table, 'description_i18n')
        op.drop_column(table, 'title_i18n')
    op.drop_column('learning_sessions', 'locale')
