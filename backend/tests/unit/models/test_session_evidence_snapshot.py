import pytest
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_equal, assert_true

pytestmark = [pytest.mark.unit]


class TestSessionEvidenceSnapshot:
    @autotest.num("1975")
    @autotest.external_id("811b4689-f44f-4e9d-af1c-43cf7dcc2e4d")
    @autotest.name("SessionEvidenceSnapshot: таблица содержит все обязательные колонки")
    def test_811b4689_model_columns_present(self):
        with autotest.step("Act: получить имена колонок модели"):
            from models.session_evidence_snapshot import SessionEvidenceSnapshot
            cols = set(SessionEvidenceSnapshot.__table__.columns.keys())

        with autotest.step("Assert: обязательные колонки присутствуют, имя таблицы верно"):
            assert_true(
                {"id", "session_id", "user_id", "lab_slug", "ts", "kind", "payload", "created_at"} <= cols,
                f"обязательные колонки присутствуют; есть {cols}",
            )
            assert_equal(
                SessionEvidenceSnapshot.__tablename__, "session_evidence_snapshots", "имя таблицы"
            )
