import pytest
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_equal, assert_is_none, assert_true

from observability.redact import redact

pytestmark = [pytest.mark.unit]


class TestRedact:
    @autotest.num("303")
    @autotest.external_id("8012810e-a673-42a5-90cb-74c11c14bf8e")
    @autotest.name("redact: masks secrets and truncates strings")
    def test_8012810e_redacts_secrets_and_truncates(self):
        with autotest.step("Redact a dict with a secret and a long string"):
            out = redact({"api_key": "sk-secret", "note": "x" * 1000, "ok": 5})
        with autotest.step("Check api_key masking"):
            assert_equal(out["api_key"], "***", "api key")
        with autotest.step("Check note truncation"):
            assert_true(
                out["note"].endswith("…(truncated)") and len(out["note"]) <= 520,
                "long note is truncated and marked",
            )
        with autotest.step("Check numeric values are preserved"):
            assert_equal(out["ok"], 5, "ok")

    @autotest.num("304")
    @autotest.external_id("df26fa4e-d747-407f-81bd-51d6b1e7d940")
    @autotest.name("redact: passthrough None")
    def test_df26fa4e_none_passthrough(self):
        with autotest.step("Check None passthrough"):
            assert_is_none(redact(None), "None passes through")
