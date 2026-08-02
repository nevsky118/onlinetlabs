import pytest
from mcp_sdk.testing import autotest

from observability.redact import redact

pytestmark = [pytest.mark.unit]


@autotest.num("303")
@autotest.external_id("8012810e-a673-42a5-90cb-74c11c14bf8e")
@autotest.name("redact: masks secrets and truncates strings")
def test_8012810e_redacts_secrets_and_truncates():
    with autotest.step("Redact a dict with a secret and a long string"):
        out = redact({"api_key": "sk-secret", "note": "x" * 1000, "ok": 5})
    with autotest.step("Check api_key masking"):
        assert out["api_key"] == "***"
    with autotest.step("Check note truncation"):
        assert out["note"].endswith("…(truncated)") and len(out["note"]) <= 520
    with autotest.step("Check numeric values are preserved"):
        assert out["ok"] == 5


@autotest.num("304")
@autotest.external_id("df26fa4e-d747-407f-81bd-51d6b1e7d940")
@autotest.name("redact: passthrough None")
def test_df26fa4e_none_passthrough():
    with autotest.step("Check None passthrough"):
        assert redact(None) is None
