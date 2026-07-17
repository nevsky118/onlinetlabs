import pytest
from types import SimpleNamespace
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_equal, assert_is_none

from experiment.transfer import skill_tag

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
