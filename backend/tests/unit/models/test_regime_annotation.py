import pytest
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_equal, assert_true

pytestmark = [pytest.mark.unit]


class TestRegimeAnnotation:
    @autotest.num("1980")
    @autotest.external_id("51f61070-6a3f-47be-8b51-90a4c340d52d")
    @autotest.name("RegimeAnnotation: table has all required columns")
    def test_51f61070_model_columns_present(self):
        with autotest.step("Act: get the model's column names"):
            from models.research import RegimeAnnotation

            cols = set(RegimeAnnotation.__table__.columns.keys())

        with autotest.step("Assert: required columns present, table name correct"):
            assert_true(
                {
                    "id",
                    "session_id",
                    "coder_id",
                    "window_index",
                    "regime_label",
                    "is_gold",
                    "created_at",
                }
                <= cols,
                f"required columns present; have {cols}",
            )
            assert_equal(RegimeAnnotation.__tablename__, "regime_annotations", "table name")
