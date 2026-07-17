import pytest
from models.agent_activity_event import AgentActivityEventRow

pytestmark = [pytest.mark.unit]


def test_table_name_and_columns():
    cols = {c.name for c in AgentActivityEventRow.__table__.columns}
    assert AgentActivityEventRow.__tablename__ == "agent_activity_events"
    assert {
        "id",
        "session_id",
        "user_id",
        "ts",
        "source",
        "kind",
        "agent",
        "severity",
        "summary",
        "detail",
    } <= cols
