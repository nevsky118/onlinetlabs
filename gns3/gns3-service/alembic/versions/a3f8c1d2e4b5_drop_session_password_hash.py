"""drop session password hash

Revision ID: a3f8c1d2e4b5
Revises: b9bc17963aae
Create Date: 2026-06-02 10:00:00.000000

The `gns3_password_hash` column is no longer used. The GNS3 account password is
handed to the student right away and the service does not need it for subsequent
authentication, which is done via the admin JWT.
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "a3f8c1d2e4b5"
down_revision: str | Sequence[str] | None = "b9bc17963aae"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_column("sessions", "gns3_password_hash")


def downgrade() -> None:
    op.add_column(
        "sessions",
        sa.Column("gns3_password_hash", sa.String(length=256), nullable=True),
    )
