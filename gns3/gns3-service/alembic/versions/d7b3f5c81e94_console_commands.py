"""console_commands

Revision ID: d7b3f5c81e94
Revises: c4e1a7d93b02
Create Date: 2026-09-09 11:02:33.914207

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "d7b3f5c81e94"
down_revision: str | Sequence[str] | None = "c4e1a7d93b02"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "console_commands",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("session_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("node_id", sa.String(length=64), nullable=False),
        sa.Column("connection_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("seq", sa.BigInteger(), nullable=False),
        sa.Column("prompt", sa.String(length=255), nullable=True),
        sa.Column("command", sa.Text(), nullable=False),
        sa.Column("response", sa.Text(), nullable=False),
        sa.Column("ts", sa.DateTime(timezone=True), nullable=False),
        sa.Column("duration_ms", sa.Float(), nullable=True),
        sa.ForeignKeyConstraint(["session_id"], ["sessions.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_console_commands_session_id", "console_commands", ["session_id"])
    op.create_index("ix_console_commands_session_ts", "console_commands", ["session_id", "ts"])
    op.create_index(
        "ix_console_commands_connection_seq", "console_commands", ["connection_id", "seq"]
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("ix_console_commands_connection_seq", table_name="console_commands")
    op.drop_index("ix_console_commands_session_ts", table_name="console_commands")
    op.drop_index("ix_console_commands_session_id", table_name="console_commands")
    op.drop_table("console_commands")
