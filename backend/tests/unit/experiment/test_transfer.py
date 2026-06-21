import pytest
from types import SimpleNamespace
from experiment.transfer import skill_tag, is_l2_pair

pytestmark = [pytest.mark.unit]


def _lab(slug, skill):
    return SimpleNamespace(slug=slug, meta={"skill": skill})


def test_skill_tag():
    assert skill_tag(_lab("a", "ip")) == "ip"
    assert skill_tag(SimpleNamespace(slug="x", meta=None)) is None
    assert skill_tag(SimpleNamespace(slug="x", meta={})) is None


def test_near_transfer_pair():
    # реальная пара: lan-static-ip ↔ lan-static-ip-b, навык static-ip-addressing
    l1 = _lab("lan-static-ip", "static-ip-addressing")
    l2 = _lab("lan-static-ip-b", "static-ip-addressing")
    assert is_l2_pair(l1, l2) is True
    assert is_l2_pair(_lab("a", "ip"), _lab("b", "routing")) is False  # разный навык
    assert is_l2_pair(l1, l1) is False  # та же лаба — не перенос
    assert is_l2_pair(_lab("a", None), _lab("b", None)) is False  # нет навыка
