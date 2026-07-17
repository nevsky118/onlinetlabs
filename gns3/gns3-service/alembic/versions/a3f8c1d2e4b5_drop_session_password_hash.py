"""drop session password hash

Revision ID: a3f8c1d2e4b5
Revises: b9bc17963aae
Create Date: 2026-06-02 10:00:00.000000

Колонка `gns3_password_hash` больше не используется: пароль GNS3-учётки
сразу выдаётся студенту и не нужен сервису для последующей аутентификации,
которая делается через admin-JWT.
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
