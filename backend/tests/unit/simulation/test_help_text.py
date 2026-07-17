"""HelpTextGen: текст просьбы студента — LLM (gated) с бюджет-гардом и шаблон-фолбэком."""
from unittest.mock import AsyncMock

import pytest
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_equal, assert_true

pytestmark = [pytest.mark.unit]


def _profile():
    from simulation.profiles import StudentProfile
    return StudentProfile(
        skill=0.3, persistence=0.4, strategy=0.3, pace=0.5, help_propensity=0.6
    )


def _generator(**overrides):
    from simulation.help_text import HelpTextGen
    params = dict(llm_enabled=True, budget_rub=100.0, price_per_1k_rub=1.0)
    params.update(overrides)
    return HelpTextGen(**params)


class TestHelpTextGen:
    @autotest.num("2037")
    @autotest.external_id("af9dbd60-797f-4540-9317-e78b2e3391b3")
    @autotest.name("help_text: LLM выключен → шаблон, вызова модели нет")
    async def test_af9dbd60_disabled_uses_template_without_llm(self):
        with autotest.step("Arrange: генератор с выключенным LLM"):
            llm = AsyncMock()
            generator = _generator(llm_enabled=False, llm_call=llm)

        with autotest.step("Act: просим сгенерировать текст"):
            text = await generator.generate(_profile(), {"step": "vlan"})

        with autotest.step("Assert: текст есть, модель не дёргалась"):
            assert_true(isinstance(text, str) and bool(text), "непустой текст")
            llm.assert_not_called()

    @autotest.num("2038")
    @autotest.external_id("1dd2ce5d-3e84-4e3f-8389-08cedbf49ec9")
    @autotest.name("help_text: LLM включён → текст от модели, расход накапливается")
    async def test_1dd2ce5d_enabled_calls_llm_and_accumulates_cost(self):
        with autotest.step("Arrange: LLM возвращает текст и 200 токенов"):
            llm = AsyncMock(return_value=("помоги с vlan", 200))
            generator = _generator(
                llm_enabled=True, budget_rub=100.0, price_per_1k_rub=1.0, llm_call=llm
            )

        with autotest.step("Act: генерируем текст"):
            text = await generator.generate(_profile(), {"step": "vlan"})

        with autotest.step("Assert: текст от модели, потрачено по прайсу"):
            assert_equal(text, "помоги с vlan", "текст")
            llm.assert_awaited_once()
            assert_true(
                generator.spent_rub == pytest.approx(200 / 1000 * 1.0), "накопленный расход"
            )

    @autotest.num("2039")
    @autotest.external_id("94b1539c-de71-4e1b-8f56-e7440b80dade")
    @autotest.name("help_text: бюджет исчерпан → шаблон, модель больше не зовётся")
    async def test_94b1539c_budget_exceeded_falls_back_to_template(self):
        with autotest.step("Arrange: бюджет 1₽, один вызов стоит 2₽"):
            llm = AsyncMock(return_value=("текст", 200))
            generator = _generator(
                llm_enabled=True, budget_rub=1.0, price_per_1k_rub=10.0, llm_call=llm
            )

        with autotest.step("Act: генерируем дважды"):
            await generator.generate(_profile(), {})  # LLM: расход → 2.0
            await generator.generate(_profile(), {})  # бюджет исчерпан → шаблон

        with autotest.step("Assert: модель вызвана ровно один раз"):
            assert_equal(llm.await_count, 1, "число вызовов LLM")

    @autotest.num("2040")
    @autotest.external_id("7f9614af-c1c7-41be-882a-61713b2ee0c1")
    @autotest.name("help_text: падение LLM не роняет прогон — уходим в шаблон")
    async def test_7f9614af_llm_error_falls_back_to_template(self):
        with autotest.step("Arrange: LLM недоступен"):
            llm = AsyncMock(side_effect=RuntimeError("llm down"))
            generator = _generator(llm_enabled=True, llm_call=llm)

        with autotest.step("Act: генерируем текст"):
            text = await generator.generate(_profile(), {})

        with autotest.step("Assert: получен шаблонный текст, исключения нет"):
            assert_true(isinstance(text, str) and bool(text), "непустой текст-фолбэк")

    @autotest.num("2042")
    @autotest.external_id("51370611-9947-470b-9fcb-f5d93c03508f")
    @autotest.name("help_text: просьбы подряд не повторяются дословно (чат не зациклен)")
    async def test_51370611_consecutive_asks_are_not_identical(self):
        with autotest.step("Arrange: генератор на шаблонах, один и тот же студент"):
            generator = _generator(llm_enabled=False)
            profile = _profile()

        with autotest.step("Act: студент просит помощь 4 раза подряд"):
            texts = [
                await generator.generate(
                    profile, {"step": "pc-ips", "node": "PC1",
                              "tried": "ip 192.168.2.11/24", "attempt": attempt}
                )
                for attempt in range(4)
            ]

        with autotest.step("Assert: все формулировки разные"):
            assert_equal(len(set(texts)), 4, "уникальных формулировок")

    @autotest.num("2043")
    @autotest.external_id("2209167b-acac-48c9-ab71-faa31a4af823")
    @autotest.name("help_text: просьба содержит контекст — узел и введённую команду")
    async def test_2209167b_ask_carries_dialogue_context(self):
        with autotest.step("Arrange: генератор на шаблонах"):
            generator = _generator(llm_enabled=False)

        with autotest.step("Act: просим помощь со второй попытки (есть что рассказать)"):
            text = await generator.generate(
                _profile(),
                {"step": "pc-ips", "node": "PC1", "tried": "ip 192.168.2.11/24",
                 "attempt": 1},
            )

        with autotest.step("Assert: в тексте упомянут узел (диалог не абстрактный)"):
            assert_true("PC1" in text, f"узел не упомянут: {text}")
