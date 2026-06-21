import pytest
from types import SimpleNamespace
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_equal, assert_true, assert_is_none

from experiment.transfer import skill_tag, is_l2_pair

pytestmark = [pytest.mark.unit]


def _lab(slug, skill):
    return SimpleNamespace(slug=slug, meta={"skill": skill})


class TestTransfer:
    @autotest.num("1062")
    @autotest.external_id("c010ee28-5cda-4fee-a19c-d3f9b5d4b46b")
    @autotest.name("skill_tag: возвращает навык или None")
    def test_c010ee28_skill_tag(self):
        with autotest.step("Act: skill_tag с навыком"):
            tag = skill_tag(_lab("a", "ip"))
        with autotest.step("Assert: навык возвращён"):
            assert_equal(tag, "ip", "skill_tag вернул ip")
        with autotest.step("Act+Assert: meta=None → None"):
            assert_is_none(skill_tag(SimpleNamespace(slug="x", meta=None)), "meta=None → None")
        with autotest.step("Act+Assert: meta={} → None"):
            assert_is_none(skill_tag(SimpleNamespace(slug="x", meta={})), "meta={} → None")

    @autotest.num("1063")
    @autotest.external_id("1d03e803-14fb-4544-9e8c-0558b9cf177e")
    @autotest.name("is_l2_pair: корректно определяет near-transfer пары")
    def test_1d03e803_near_transfer_pair(self):
        with autotest.step("Arrange: реальная L1/L2 пара одного навыка"):
            l1 = _lab("lan-static-ip", "static-ip-addressing")
            l2 = _lab("lan-static-ip-b", "static-ip-addressing")
        with autotest.step("Assert: l1↔l2 — пара"):
            assert_true(is_l2_pair(l1, l2) is True, "l1/l2 — near-transfer пара")
        with autotest.step("Assert: разный навык — не пара"):
            assert_true(is_l2_pair(_lab("a", "ip"), _lab("b", "routing")) is False, "разный навык")
        with autotest.step("Assert: та же лаба — не пара"):
            assert_true(is_l2_pair(l1, l1) is False, "та же лаба не перенос")
        with autotest.step("Assert: нет навыка — не пара"):
            assert_true(is_l2_pair(_lab("a", None), _lab("b", None)) is False, "нет навыка")
