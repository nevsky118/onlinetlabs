import pytest
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_equal, assert_true

pytestmark = [pytest.mark.unit]


class TestRegimeAnnotation:
    @autotest.num("1980")
    @autotest.external_id("51f61070-6a3f-47be-8b51-90a4c340d52d")
    @autotest.name("RegimeAnnotation: таблица содержит все обязательные колонки")
    def test_51f61070_model_columns_present(self):
        with autotest.step("Act: получить имена колонок модели"):
            from models.regime_annotation import RegimeAnnotation
            cols = set(RegimeAnnotation.__table__.columns.keys())

        with autotest.step("Assert: обязательные колонки присутствуют, имя таблицы верно"):
            assert_true(
                {"id", "session_id", "coder_id", "window_index", "regime_label", "is_gold", "created_at"} <= cols,
                f"обязательные колонки присутствуют; есть {cols}",
            )
            assert_equal(RegimeAnnotation.__tablename__, "regime_annotations", "имя таблицы")
