"""unique attempt number, and the enrolled_at index the browser sorts by

Revision ID: 4f2c8b90d1a3
Revises: 3d6a91c7e04b
Create Date: 2026-08-29 16:00:00.000000
"""
from typing import Sequence, Union

from alembic import op

revision: str = '4f2c8b90d1a3'
down_revision: Union[str, None] = '3d6a91c7e04b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # max-plus-one takes no lock under Read Committed, so duplicates already exist
    # wherever two attempts raced. Renumber them before the constraint can hold.
    op.execute(
        """
        WITH renumbered AS (
            SELECT id, row_number() OVER (
                PARTITION BY user_id, lab_slug, step_slug ORDER BY started_at, id
            ) AS n
            FROM step_attempts
        )
        UPDATE step_attempts AS s
        SET attempt_number = r.n
        FROM renumbered AS r
        WHERE s.id = r.id AND s.attempt_number IS DISTINCT FROM r.n
        """
    )
    op.create_unique_constraint(
        "uq_step_attempts_number",
        "step_attempts",
        ["user_id", "lab_slug", "step_slug", "attempt_number"],
    )
    op.create_index("ix_study_participants_enrolled_at", "study_participants", ["enrolled_at"])


def downgrade() -> None:
    op.drop_index("ix_study_participants_enrolled_at", table_name="study_participants")
    op.drop_constraint("uq_step_attempts_number", "step_attempts", type_="unique")
