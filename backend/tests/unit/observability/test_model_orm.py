import pytest
from mcp_sdk.testing import autotest

from models.agent_activity_event import AgentActivityEventRow

pytestmark = [pytest.mark.unit]


@autotest.num("3250")
@autotest.external_id("e4adbf3b-718a-4324-88ff-3ace68a7bf6d")
@autotest.name("AgentActivityEventRow: table name and expected columns")
def test_e4adbf3b_table_name_and_columns():
    with autotest.step("Act: collect column names from the mapped table"):
        cols = {c.name for c in AgentActivityEventRow.__table__.columns}

    with autotest.step("Assert: table name and the expected columns are present"):
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
