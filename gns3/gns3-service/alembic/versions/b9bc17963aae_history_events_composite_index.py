"""history_events composite index

Revision ID: b9bc17963aae
Revises: e5bb89c9af4d
Create Date: 2026-05-31 11:22:11.705027

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b9bc17963aae"
down_revision: str | Sequence[str] | None = "e5bb89c9af4d"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_index(
        "ix_history_events_session_ts",
        "history_events",
        ["session_id", sa.text("timestamp DESC")],
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("ix_history_events_session_ts", table_name="history_events")
