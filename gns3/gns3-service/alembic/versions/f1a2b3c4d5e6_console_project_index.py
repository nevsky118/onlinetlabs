"""console project index

Revision ID: f1a2b3c4d5e6
Revises: d7b3f5c81e94
Create Date: 2026-09-11 00:00:00.000000

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "f1a2b3c4d5e6"
down_revision: str | Sequence[str] | None = "d7b3f5c81e94"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

INDEXES = (
    ("ix_sessions_gns3_project_id", "sessions", ["gns3_project_id"]),
    ("ix_console_chunks_ts", "console_chunks", ["ts"]),
    ("ix_console_commands_ts", "console_commands", ["ts"]),
)


def upgrade() -> None:
    """Upgrade schema."""
    with op.get_context().autocommit_block():
        for index_name, table_name, columns in INDEXES:
            # Clears an INVALID leftover build.
            op.drop_index(
                index_name,
                table_name=table_name,
                if_exists=True,
                postgresql_concurrently=True,
            )
            op.create_index(
                index_name,
                table_name,
                columns,
                if_not_exists=True,
                postgresql_concurrently=True,
            )


def downgrade() -> None:
    """Downgrade schema."""
    with op.get_context().autocommit_block():
        for index_name, table_name, _ in reversed(INDEXES):
            op.drop_index(
                index_name,
                table_name=table_name,
                if_exists=True,
                postgresql_concurrently=True,
            )
