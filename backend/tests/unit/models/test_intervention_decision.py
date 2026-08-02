import pytest
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_equal, assert_true

pytestmark = [pytest.mark.unit]


class TestInterventionDecision:
    @autotest.num("1966")
    @autotest.external_id("ff5ef85c-5fd8-4c3f-9706-c604f0828a8b")
    @autotest.name("InterventionDecision: table has all required columns")
    def test_ff5ef85c_model_columns_present(self):
        with autotest.step("Act: get the model's column names"):
            from models.intervention_decision import InterventionDecision

            cols = set(InterventionDecision.__table__.columns.keys())

        with autotest.step("Assert: all required columns present, table name correct"):
            assert_true(
                {
                    "id",
                    "session_id",
                    "user_id",
                    "lab_slug",
                    "spell_id",
                    "ts",
                    "regime",
                    "dwell_seconds",
                    "t_k_applied",
                    "assignment",
                    "subsequent_exit_ts",
                    "censored",
                    "created_at",
                }
                <= cols,
                f"all required columns present; have: {cols}",
            )
            assert_equal(InterventionDecision.__tablename__, "intervention_decisions", "table name")
