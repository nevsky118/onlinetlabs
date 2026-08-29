"""mcp_audit: timestamp index for the retention sweep

Revision ID: 2a5f9d4c8e13
Revises: 6e3b8a1f7c92
Create Date: 2026-08-29 10:20:00.000000
"""
from typing import Sequence, Union

from alembic import op

revision: str = '2a5f9d4c8e13'
down_revision: Union[str, None] = '6e3b8a1f7c92'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # retention delete would otherwise seq-scan
    op.create_index('ix_mcp_audit_ts', 'mcp_audit', ['ts'])


def downgrade() -> None:
    op.drop_index('ix_mcp_audit_ts', table_name='mcp_audit')
