"""Regression: run_validation must resolve locale-map step titles, not leak the raw dict."""

import pytest
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_equal, assert_is_instance

from validation.runner import run_validation

pytestmark = [pytest.mark.unit]


class TestRunValidationLocalizedTitle:
    @autotest.num("3140")
    @autotest.external_id("b11e4bbc-964a-4a7f-96d6-ced55420be81")
    @autotest.name(
        "run_validation: a locale-map step title resolves to a string in the requested locale"
    )
    async def test_b11e4bbc_locale_map_title_resolves_to_string(self):
        with autotest.step("Arrange: a spec whose step title is a locale map, no checks needed"):
            spec = {
                "steps": [
                    {
                        "id": "configure-pc1",
                        "title": {"en": "Configure PC1", "ru": "Настроить PC1"},
                        "checks": [],
                    }
                ]
            }

        with autotest.step(
            "Act: run validation in ru and en, collect the emitted and persisted titles"
        ):
            results: dict[str, tuple[str, str]] = {}
            for locale in ("ru", "en"):
                emitted_title = None
                persisted_steps: list = []
                async for event, steps_snapshot in run_validation(
                    ctx=object(), spec=spec, locale=locale
                ):
                    if event.type == "step.start":
                        emitted_title = event.data["title"]
                    if event.type == "run.finish":
                        persisted_steps = steps_snapshot
                results[locale] = (emitted_title, persisted_steps[0]["title"])

        with autotest.step(
            "Assert: both surfaces carry a resolved string in the requested locale, not a dict"
        ):
            ru_emitted, ru_persisted = results["ru"]
            en_emitted, en_persisted = results["en"]
            assert_is_instance(
                ru_emitted, str, "SSE step.start title is a string, not a locale map"
            )
            assert_is_instance(
                ru_persisted,
                str,
                "persisted validation_runs.steps title is a string, not a locale map",
            )
            assert_equal(
                ru_emitted, "Настроить PC1", "SSE title resolves to the requested ru locale"
            )
            assert_equal(
                ru_persisted, "Настроить PC1", "persisted title resolves to the requested ru locale"
            )
            assert_equal(
                en_emitted, "Configure PC1", "SSE title resolves to the requested en locale"
            )
            assert_equal(
                en_persisted, "Configure PC1", "persisted title resolves to the requested en locale"
            )
