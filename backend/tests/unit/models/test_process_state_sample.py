import pytest

from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_equal, assert_true

pytestmark = [pytest.mark.unit]


class TestProcessStateSample:
    @autotest.num("1602")
    @autotest.external_id("cd5f06eb-696f-47bf-bbb0-d604802d854a")
    @autotest.name("ProcessStateSample: таблица содержит все обязательные колонки")
    def test_cd5f06eb_model_columns_present(self):
        with autotest.step("Act: получить имена колонок модели"):
            from models.process_state_sample import ProcessStateSample

            cols = set(ProcessStateSample.__table__.columns.keys())

        with autotest.step("Assert: все обязательные колонки присутствуют, имя таблицы верно"):
            assert_true(
                {
                    "id",
                    "session_id",
                    "user_id",
                    "lab_slug",
                    "ts",
                    "regime",
                    "dwell_seconds",
                    "created_at",
                }
                <= cols,
                "все обязательные колонки присутствуют",
            )
            assert_equal(ProcessStateSample.__tablename__, "process_state_samples", "имя таблицы")
