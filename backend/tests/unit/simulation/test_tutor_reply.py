"""Ответ тьютора в чат-логе: фолбэк прогрессивный, а не одна замороженная фраза.

Регрессия: шаблон выбирался как `len(question) % N`, а вопрос студента был константным →
тьютор дословно повторял один и тот же ответ, и диалог в чат-вьюере зацикливался.
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
    @autotest.name("tutor_reply: при недоступном LLM ответы по попыткам не повторяются")
    async def test_70b076e0_fallback_is_progressive_not_repeated(self):
        with autotest.step("Arrange: LLM недоступен → работает шаблон-фолбэк"):
            context = {"node": "PC1", "tried": "ip 192.168.2.11/24"}
            # build_client связывается при создании замыкания → патчим ДО его создания,
            # иначе юнит-тест пойдёт в реальный YandexGPT.
            patcher = patch("llm.client.build_client", side_effect=RuntimeError("llm down"))

        with autotest.step("Act: студент обращается 4 раза подряд"):
            with patcher:
                reply = _make_tutor_reply(_settings_stub(), "lan-static-ip")
                answers = [
                    await reply(
                        "Не пойму, что не так на PC1. Подскажешь?",
                        {**context, "attempt": attempt},
                    )
                    for attempt in range(4)
                ]

        with autotest.step("Assert: каждая реплика тьютора своя, все — про узел"):
            assert_equal(len(set(answers)), 4, "уникальных ответов тьютора")
            for answer in answers:
                assert_true("PC1" in answer, f"ответ без контекста узла: {answer}")
