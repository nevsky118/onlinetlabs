"""history_events_notify_trigger

Revision ID: e5bb89c9af4d
Revises: 7338a2aa871f
Create Date: 2026-05-30 17:15:46.843874

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e5bb89c9af4d'
down_revision: Union[str, Sequence[str], None] = '7338a2aa871f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        CREATE OR REPLACE FUNCTION notify_history_event() RETURNS trigger AS $$
        BEGIN
            PERFORM pg_notify(
                'history_events',
                json_build_object(
                    'session_id', NEW.session_id::text,
                    'event_type', NEW.event_type,
                    'component_id', NEW.component_id,
                    'timestamp', NEW.timestamp::text,
                    'data', NEW.data
                )::text
            );
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
        """
    )
    op.execute(
        """
        CREATE TRIGGER history_events_notify_trigger
        AFTER INSERT ON history_events
        FOR EACH ROW EXECUTE FUNCTION notify_history_event();
        """
    )


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS history_events_notify_trigger ON history_events;")
    op.execute("DROP FUNCTION IF EXISTS notify_history_event();")
