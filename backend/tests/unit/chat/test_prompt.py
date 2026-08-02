import pytest
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_equal, assert_true

from chat.prompt import LAB_STATE_MARKER, TASK_MARKER, build_system_content

pytestmark = [pytest.mark.unit]


class TestBuildSystemContent:
    @autotest.num("3128")
    @autotest.external_id("815f5f51-5be3-4a60-a14d-fe2dff17d823")
    @autotest.name("build_system_content: markers are identical across locales")
    def test_815f5f51_markers_locale_invariant(self):
        with autotest.step("Act: assemble the prompt in both locales with both sections present"):
            en = build_system_content("en", "lab text", "state text")
            ru = build_system_content("ru", "lab text", "state text")

        with autotest.step("Assert: both carry the same ASCII markers"):
            for rendered in (en, ru):
                assert_true(TASK_MARKER in rendered, "the task marker is present")
                assert_true(LAB_STATE_MARKER in rendered, "the lab state marker is present")
            assert_equal(TASK_MARKER, "[TASK]", "the task marker is ASCII and stable")
            assert_equal(
                LAB_STATE_MARKER, "[LAB_STATE]", "the lab state marker is ASCII and stable"
            )

    @autotest.num("3129")
    @autotest.external_id("b0c36f9a-5735-41df-baf0-a918553f95b1")
    @autotest.name("build_system_content: the system prompt body is translated")
    def test_b0c36f9a_body_translated(self):
        with autotest.step("Act: assemble the prompt in both locales"):
            en = build_system_content("en", None, None)
            ru = build_system_content("ru", None, None)

        with autotest.step("Assert: the bodies differ"):
            assert_true(en != ru, "the system prompt body is locale-specific")

    @autotest.num("3130")
    @autotest.external_id("1247be0c-a33d-47ae-a9f2-ac74034fae60")
    @autotest.name("build_system_content: the prompt names the sections it will receive")
    def test_1247be0c_prompt_references_its_markers(self):
        with autotest.step("Act: assemble with no context sections at all, in both locales"):
            rendered_by_locale = {
                locale: build_system_content(locale, None, None) for locale in ("en", "ru")
            }

        with autotest.step("Assert: each locale's body still refers to both markers by name"):
            for locale, rendered in rendered_by_locale.items():
                assert_true(
                    rendered.count(TASK_MARKER) >= 1,
                    f"{locale}: the body references the task marker",
                )
                assert_true(
                    rendered.count(LAB_STATE_MARKER) >= 1,
                    f"{locale}: the body references the state marker",
                )

    @autotest.num("3131")
    @autotest.external_id("bccfe71f-eed5-4867-8cf3-e12c6839b2e6")
    @autotest.name("build_system_content: absent sections are omitted, not left empty")
    def test_bccfe71f_absent_sections_omitted(self):
        with autotest.step("Act: assemble with only the lab section"):
            rendered = build_system_content("en", "lab text", None)

        with autotest.step("Assert: the state section header is not appended without content"):
            assert_true("lab text" in rendered, "the provided section is appended")
            assert_true(f"\n\n{LAB_STATE_MARKER}\n" not in rendered, "no empty state section")

    @autotest.num("3132")
    @autotest.external_id("f744ee65-f944-4355-b960-23b889afb1f3")
    @autotest.name("build_system_content: the language directive names the target language")
    def test_f744ee65_language_directive(self):
        with autotest.step("Act: assemble in both locales"):
            en = build_system_content("en", None, None)
            ru = build_system_content("ru", None, None)

        with autotest.step("Assert: each names its own language"):
            assert_true("English" in en, "the English prompt names English")
            assert_true("русском" in ru, "the Russian prompt names Russian")
