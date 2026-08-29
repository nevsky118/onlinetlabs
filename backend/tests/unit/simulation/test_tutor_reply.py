"""Tutor reply in the chat log: fallback is progressive, not one frozen phrase.

Regression: template was picked as `len(question) % N`, and the student's question was constant →
the tutor repeated the exact same answer verbatim, and the dialogue in the chat viewer looped.
"""

from unittest.mock import MagicMock, patch

import pytest
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_equal, assert_true

from simulation.run import _make_tutor_reply

pytestmark = [pytest.mark.unit]


def _settings_stub():
    settings = MagicMock()
    settings.agents.chat_model = "legacy-default"
    return settings


class TestTutorReplyFallback:
    @autotest.num("2044")
    @autotest.external_id("70b076e0-1de0-4010-a9ac-932dd978e557")
    @autotest.name("tutor_reply: when the LLM is unavailable, replies across attempts don't repeat")
    async def test_70b076e0_fallback_is_progressive_not_repeated(self):
        with autotest.step("Arrange: LLM unavailable → template fallback kicks in"):
            context = {"node": "PC1", "tried": "ip 192.168.2.11/24"}
            # patch where simulation.run binds it, else the test hits the real YandexGPT
            patcher = patch("simulation.run.build_client", side_effect=RuntimeError("llm down"))

        with autotest.step("Act: student reaches out 4 times in a row"):
            with patcher:
                reply = _make_tutor_reply(_settings_stub(), "lan-static-ip")
                answers = [
                    await reply(
                        "Не пойму, что не так на PC1. Подскажешь?",
                        {**context, "attempt": attempt},
                    )
                    for attempt in range(4)
                ]

        with autotest.step("Assert: each tutor reply is unique, all about the node"):
            assert_equal(len(set(answers)), 4, "unique tutor replies")
            for answer in answers:
                assert_true("PC1" in answer, f"reply missing node context: {answer}")
