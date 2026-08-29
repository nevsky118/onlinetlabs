"""Every step a validator checks must be something the lab page actually asked for."""

from pathlib import Path

import pytest
import yaml
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_equal

pytestmark = [pytest.mark.unit]

_BACKEND = Path(__file__).resolve().parents[3]
_SPEC_DIR = _BACKEND / "validation" / "labs"
_CONTENT_DIR = _BACKEND.parent / "frontend" / "apps" / "web" / "content" / "labs"

# Wire-level artefacts a learner is never told to type.
_NOT_USER_FACING = {"0.0.0.0"}
_NODE_KEYS = ("node", "from", "to_node")
_ADDRESS_KEYS = ("to",)
_EXPECT_KEYS = ("ip", "gateway", "subnet")


def _specs() -> list[Path]:
    """Every lab spec on disk."""
    return sorted(_SPEC_DIR.glob("*.yaml"))


def _referenced_terms(spec: dict) -> set[str]:
    """Node names and literal addresses the spec's checks depend on."""
    terms: set[str] = set()
    for step in spec.get("steps") or []:
        for check in step.get("checks") or []:
            for key in _NODE_KEYS + _ADDRESS_KEYS:
                declared = check.get(key)
                if isinstance(declared, str):
                    terms.add(declared)
            for key in _EXPECT_KEYS:
                declared = (check.get("expect") or {}).get(key)
                if isinstance(declared, str):
                    terms.add(declared.split("/", 1)[0])
    return {term for term in terms if term and term not in _NOT_USER_FACING}


def _content_for(slug: str) -> dict[str, str]:
    """The lab page text per locale."""
    directory = _CONTENT_DIR / slug
    return {
        path.name: path.read_text(encoding="utf-8")
        for path in sorted(directory.glob("index.*.mdx"))
    }


class TestSpecMatchesContent:
    @autotest.num("3442")
    @autotest.external_id("90e62856-9d2d-4fad-a51d-d3234ae8e57f")
    @autotest.name("every lab spec has content in both locales")
    def test_90e62856_every_spec_has_content(self):
        with autotest.step("Act: pair each spec with its lab page"):
            missing = {}
            for spec_path in _specs():
                slug = spec_path.stem
                pages = _content_for(slug)
                if len(pages) < 2:
                    missing[slug] = sorted(pages)

        with autotest.step("Assert: every lab is documented in en and ru"):
            assert_equal(missing, {}, "content present")

    @autotest.num("3443")
    @autotest.external_id("59be1de7-efdb-45dd-808b-419355b9b4fe")
    @autotest.name("a validator never checks something the lab page never mentions")
    def test_59be1de7_checked_terms_are_documented(self):
        with autotest.step("Act: compare each spec's referenced terms against its page text"):
            undocumented: dict[str, list[str]] = {}
            for spec_path in _specs():
                slug = spec_path.stem
                spec = yaml.safe_load(spec_path.read_text(encoding="utf-8"))
                pages = _content_for(slug)
                for term in sorted(_referenced_terms(spec)):
                    absent = [name for name, text in pages.items() if term not in text]
                    if absent:
                        undocumented.setdefault(slug, []).append(f"{term} missing from {absent}")

        with autotest.step("Assert: nothing is checked that the learner was not told about"):
            assert_equal(undocumented, {}, "specs and content agree")

    @autotest.num("3444")
    @autotest.external_id("b0706ed1-dc58-4251-91c2-3835894c29a7")
    @autotest.name("every lab page tells the learner to run the validator")
    def test_b0706ed1_pages_mention_validation(self):
        with autotest.step("Arrange: the heading each locale uses for the validator step"):
            markers = {"en": "## Validation", "ru": "## Проверка"}

        with autotest.step("Act: look for it in every lab page"):
            missing: dict[str, list[str]] = {}
            for spec_path in _specs():
                slug = spec_path.stem
                for name, text in _content_for(slug).items():
                    locale = name.split(".")[1]
                    marker = markers.get(locale)
                    if marker and marker not in text:
                        missing.setdefault(slug, []).append(name)

        with autotest.step("Assert: no lab leaves the learner without the last step"):
            assert_equal(missing, {}, "validation section present")
