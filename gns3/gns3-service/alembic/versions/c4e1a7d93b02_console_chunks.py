"""console_chunks

Revision ID: c4e1a7d93b02
Revises: a3f8c1d2e4b5
Create Date: 2026-09-09 10:14:52.113408

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c4e1a7d93b02"
down_revision: str | Sequence[str] | None = "a3f8c1d2e4b5"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "console_chunks",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("session_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("node_id", sa.String(length=64), nullable=False),
        sa.Column("connection_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("seq", sa.BigInteger(), nullable=False),
        sa.Column("direction", sa.String(length=3), nullable=False),
        sa.Column("payload", sa.LargeBinary(), nullable=False),
        sa.Column("truncated", sa.Boolean(), nullable=False),
        sa.Column("redacted", sa.Boolean(), nullable=False),
        sa.Column("ts", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["session_id"], ["sessions.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_console_chunks_session_id", "console_chunks", ["session_id"])
    op.create_index("ix_console_chunks_connection_seq", "console_chunks", ["connection_id", "seq"])
    op.create_index("ix_console_chunks_session_ts", "console_chunks", ["session_id", "ts"])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("ix_console_chunks_session_ts", table_name="console_chunks")
    op.drop_index("ix_console_chunks_connection_seq", table_name="console_chunks")
    op.drop_index("ix_console_chunks_session_id", table_name="console_chunks")
    op.drop_table("console_chunks")
