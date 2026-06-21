import pytest

from observability.redact import redact
from mcp_sdk.testing import autotest

pytestmark = [pytest.mark.unit]


@autotest.num("303")
@autotest.external_id("f6a7b8c9-d0e1-4f2a-3b4c-5d6e7f8a9b0c")
@autotest.name("redact: маскирует секреты и обрезает строки")
def test_redacts_secrets_and_truncates():
    with autotest.step("Редактируем dict с секретом и длинной строкой"):
        out = redact({"api_key": "sk-secret", "note": "x" * 1000, "ok": 5})
    with autotest.step("Проверяем маскирование api_key"):
        assert out["api_key"] == "***"
    with autotest.step("Проверяем обрезку note"):
        assert out["note"].endswith("…(truncated)") and len(out["note"]) <= 520
    with autotest.step("Проверяем сохранение числовых значений"):
        assert out["ok"] == 5


@autotest.num("304")
@autotest.external_id("a7b8c9d0-e1f2-4a3b-5c6d-7e8f9a0b1c2d")
@autotest.name("redact: passthrough None")
def test_none_passthrough():
    with autotest.step("Проверяем None passthrough"):
        assert redact(None) is None
