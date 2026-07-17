"""GNS3Actor: student action → device console config / chat / idle.

The console is the channel that spec checks read (`vpcs.show_ip`), and their failures feed
the regime detector (`check_failing` → error_repeat_count).
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from mcp_sdk.testing import autotest
from mcp_sdk.testing.custom_assertions import assert_equal, assert_true

from simulation.lab_config import NodeTask

pytestmark = [pytest.mark.unit]

_TASKS = [
    NodeTask(node="PC1", correct_cmd="ip 192.168.1.11/24", wrong_cmd="ip 192.168.2.11/24"),
    NodeTask(node="PC2", correct_cmd="ip 192.168.1.12/24", wrong_cmd="ip 192.168.2.12/24"),
]
_CONSOLES = {"PC1": ("localhost", 5000), "PC2": ("localhost", 5001)}


class _FakeDb:
    async def __aenter__(self):
        return self

    async def __aexit__(self, *a):
        return False


def _make_actor(save_user_message=None):
    from simulation.env.gns3_actor import GNS3Actor
    from simulation.help_text import HelpTextGen
    from simulation.profiles import StudentProfile

    return GNS3Actor(
        node_tasks=_TASKS,
        consoles=_CONSOLES,
        db_factory=lambda: _FakeDb(),
        backend_session_id="s1",
        help_gen=HelpTextGen(llm_enabled=False, budget_rub=0, price_per_1k_rub=0),
        profile=StudentProfile(
            skill=0.3, persistence=0.4, strategy=0.3, pace=0.5, help_propensity=0.6
        ),
        save_user_message=save_user_message or AsyncMock(),
    )


def _fake_connection():
    writer = MagicMock()
    writer.write = MagicMock()
    writer.drain = AsyncMock()
    writer.close = MagicMock()
    writer.wait_closed = AsyncMock()
    return MagicMock(), writer


def _sent_bytes(writer) -> bytes:
    return b"".join(call.args[0] for call in writer.write.call_args_list)


class TestGNS3ActorConsole:
    @autotest.num("2023")
    @autotest.external_id("88e6e5fb-a612-4a06-a94d-a7732e1556d2")
    @autotest.name("GNS3Actor: верное действие пишет эталонный IP в консоль узла")
    async def test_88e6e5fb_correct_action_writes_expected_ip(self):
        with autotest.step("Arrange: актор с задачами из спеки и фейковой консолью"):
            reader, writer = _fake_connection()
            actor = _make_actor()

        with autotest.step("Act: студент выполняет верное действие"):
            from simulation.policy import Action

            with patch(
                "asyncio.open_connection", AsyncMock(return_value=(reader, writer))
            ) as open_conn:
                await actor.execute(Action.CORRECT_CMD)

        with autotest.step("Assert: подключились к консоли PC1 и отправили эталонный IP"):
            open_conn.assert_awaited_once_with("localhost", 5000)
            assert_true(b"ip 192.168.1.11/24" in _sent_bytes(writer), "команда в консоли")

    @autotest.num("2024")
    @autotest.external_id("b71fb398-b976-4f4c-98c2-4a5445cc51d5")
    @autotest.name("GNS3Actor: верное действие продвигает студента к следующему узлу")
    async def test_b71fb398_correct_action_advances_to_next_node(self):
        with autotest.step("Arrange: актор с двумя узлами"):
            reader, writer = _fake_connection()
            actor = _make_actor()

        with autotest.step("Act: два верных действия подряд"):
            from simulation.policy import Action

            with patch("asyncio.open_connection", AsyncMock(return_value=(reader, writer))):
                await actor.execute(Action.CORRECT_CMD)
                await actor.execute(Action.CORRECT_CMD)

        with autotest.step("Assert: настроены оба узла, каждый своим адресом"):
            sent = _sent_bytes(writer)
            assert_true(b"ip 192.168.1.11/24" in sent, "PC1 настроен")
            assert_true(b"ip 192.168.1.12/24" in sent, "PC2 настроен")

    @autotest.num("2025")
    @autotest.external_id("0d243db0-7f0d-46c2-a321-f77cd789cef1")
    @autotest.name("GNS3Actor: повтор ошибки шлёт ТУ ЖЕ неверную команду (→ check_failing)")
    async def test_0d243db0_repeat_error_resends_same_wrong_command(self):
        with autotest.step("Arrange: актор с фейковой консолью"):
            reader, writer = _fake_connection()
            actor = _make_actor()

        with autotest.step("Act: студент дважды повторяет одну ошибку"):
            from simulation.policy import Action

            with patch("asyncio.open_connection", AsyncMock(return_value=(reader, writer))):
                await actor.execute(Action.REPEAT_ERROR)
                await actor.execute(Action.REPEAT_ERROR)

        with autotest.step("Assert: команда идентична, проверка упадёт с тем же actual"):
            sent = [call.args[0] for call in writer.write.call_args_list]
            assert_equal(sent, [b"ip 192.168.2.11/24\r\n", b"ip 192.168.2.11/24\r\n"], "команды")

    @autotest.num("2026")
    @autotest.external_id("c67fa9c0-9a9a-4da7-8521-b5a884e51d39")
    @autotest.name("GNS3Actor: недоступная консоль не роняет прогон")
    async def test_c67fa9c0_unreachable_console_does_not_raise(self):
        with autotest.step("Arrange: консоль отказывает в соединении"):
            actor = _make_actor()

        with autotest.step("Act: студент пробует неверную команду"):
            from simulation.policy import Action

            with patch("asyncio.open_connection", AsyncMock(side_effect=OSError("refused"))):
                await actor.execute(Action.WRONG_CMD)

        with autotest.step("Assert: исключение не пробросилось (когорта не падает)"):
            assert_true(True, "исключения не было")

    @autotest.num("2027")
    @autotest.external_id("f9472c98-ea85-4b44-9d73-14cfd0d09d89")
    @autotest.name("GNS3Actor: просьба о помощи сохраняет диалог с ответом тьютора")
    async def test_f9472c98_ask_help_saves_dialogue_with_tutor_reply(self):
        with autotest.step("Arrange: актор с сохранением сообщений и ответом тьютора"):
            save_user, save_assistant = AsyncMock(), AsyncMock()

            async def tutor_reply(question, context):
                return "Проверь маску подсети."

            actor = _make_actor(save_user_message=save_user)
            actor._save_assistant_message = save_assistant
            actor._tutor_reply = tutor_reply

        with autotest.step("Act: студент просит помощи"):
            from simulation.policy import Action

            await actor.execute(Action.ASK_HELP, help_context={"step": "ip"})

        with autotest.step("Assert: в чат-лог легли и вопрос, и ответ тьютора"):
            save_user.assert_awaited_once()
            save_assistant.assert_awaited_once()
            assert_equal(save_assistant.await_args.args[1], "s1", "session_id ответа")
            assert_equal(
                save_assistant.await_args.args[2][0]["text"],
                "Проверь маску подсети.",
                "текст ответа",
            )

    @autotest.num("2045")
    @autotest.external_id("8e6ea882-867f-4568-b42e-ad7f9de646d2")
    @autotest.name("GNS3Actor: в диалог уходят узел и команда ОДНОЙ пары (не вразнобой)")
    async def test_8e6ea882_dialogue_context_pairs_node_with_command(self):
        with autotest.step("Arrange: актор с двумя узлами и перехватом просьбы о помощи"):
            captured: dict = {}

            class _CapturingHelpGen:
                async def generate(self, profile, context):
                    captured.update(context)
                    return "вопрос"

            reader, writer = _fake_connection()
            actor = _make_actor()
            actor._help_gen = _CapturingHelpGen()

        with autotest.step("Act: студент настроил PC1, затем попросил помощь"):
            from simulation.policy import Action

            with patch("asyncio.open_connection", AsyncMock(return_value=(reader, writer))):
                await actor.execute(Action.CORRECT_CMD)  # PC1, index moved on to PC2
                await actor.execute(Action.ASK_HELP)

        with autotest.step("Assert: узел и процитированная команда про PC1"):
            assert_equal(captured.get("node"), "PC1", "узел в контексте")
            assert_equal(captured.get("tried"), "ip 192.168.1.11/24", "команда в контексте")
            assert_equal(captured.get("attempt"), 0, "номер попытки")

    @autotest.num("2028")
    @autotest.external_id("64b1b675-c9ca-44f4-8f26-c7486c20010b")
    @autotest.name("GNS3Actor: простой не трогает консоль")
    async def test_64b1b675_idle_does_not_touch_console(self):
        with autotest.step("Arrange: актор"):
            actor = _make_actor()

        with autotest.step("Act: студент простаивает"):
            from simulation.policy import Action

            with patch("asyncio.open_connection", AsyncMock()) as open_conn:
                with patch("asyncio.sleep", AsyncMock()):
                    await actor.execute(Action.IDLE)

        with autotest.step("Assert: подключения к консоли не было"):
            open_conn.assert_not_awaited()
