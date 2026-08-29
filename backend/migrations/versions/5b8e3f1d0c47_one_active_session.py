"""one active session per learner and lab, enforced by the database

Revision ID: 5b8e3f1d0c47
Revises: 7c4d2e9a6b18
Create Date: 2026-08-29 15:00:00.000000
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = '5b8e3f1d0c47'
down_revision: Union[str, None] = '7c4d2e9a6b18'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_LIVE = "('active', 'provisioning')"


def upgrade() -> None:
    # Two concurrent launches both read "no active session" and both insert; the
    # next read then raises MultipleResultsFound. End the older duplicates first,
    # or the index cannot be created.
    op.execute(
        f"""
        UPDATE learning_sessions AS s
        SET status = 'ended', ended_at = COALESCE(ended_at, now())
        WHERE s.status IN {_LIVE}
          AND EXISTS (
            SELECT 1 FROM learning_sessions AS newer
            WHERE newer.user_id = s.user_id
              AND newer.lab_slug = s.lab_slug
              AND newer.status IN {_LIVE}
              AND (newer.started_at, newer.id) > (s.started_at, s.id)
          )
        """
    )
    op.create_index(
        "uq_learning_sessions_one_live",
        "learning_sessions",
        ["user_id", "lab_slug"],
        unique=True,
        postgresql_where=sa.text(f"status IN {_LIVE}"),
    )

    op.create_index(
        "ix_step_attempts_user_lab_step",
        "step_attempts",
        ["user_id", "lab_slug", "step_slug"],
    )


def downgrade() -> None:
    op.drop_index("ix_step_attempts_user_lab_step", table_name="step_attempts")
    op.drop_index("uq_learning_sessions_one_live", table_name="learning_sessions")
