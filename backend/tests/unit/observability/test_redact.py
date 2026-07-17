import pytest
from mcp_sdk.testing import autotest

from observability.redact import redact

pytestmark = [pytest.mark.unit]


@autotest.num("303")
@autotest.external_id("8012810e-a673-42a5-90cb-74c11c14bf8e")
@autotest.name("redact: маскирует секреты и обрезает строки")
def test_8012810e_redacts_secrets_and_truncates():
    with autotest.step("Редактируем dict с секретом и длинной строкой"):
        out = redact({"api_key": "sk-secret", "note": "x" * 1000, "ok": 5})
    with autotest.step("Проверяем маскирование api_key"):
        assert out["api_key"] == "***"
    with autotest.step("Проверяем обрезку note"):
        assert out["note"].endswith("…(truncated)") and len(out["note"]) <= 520
    with autotest.step("Проверяем сохранение числовых значений"):
        assert out["ok"] == 5


@autotest.num("304")
@autotest.external_id("df26fa4e-d747-407f-81bd-51d6b1e7d940")
@autotest.name("redact: passthrough None")
def test_df26fa4e_none_passthrough():
    with autotest.step("Проверяем None passthrough"):
        assert redact(None) is None
