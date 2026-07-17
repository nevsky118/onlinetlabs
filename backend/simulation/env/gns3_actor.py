"""GNS3-исполнитель: действие студента → реальная консоль устройства / chat / idle.

КАК ЗАМЫКАЕТСЯ КОНТУР. Детектор режимов кормится провалами spec-проверок:
`LabProgressObserver` периодически гоняет проверки лабы (`vpcs.show_ip`, `vpcs.ping` —
они телнетятся в консоль узла) и эмитит `check_failing` / `check_retry` / `check_regressed`
как поведенческие события event_type=error. Отсюда берутся `error_repeat_count`,
`distinct_failing_actuals`, `cycles_failing_unchanged` — 4 из 6 правил детектора.

Поэтому студент КОНФИГУРИРУЕТ устройство в консоли (верная команда → проверка проходит,
неверная → падает), а узлы остаются запущенными: потушенный узел = недоступная консоль
= проверки просто висят, и сигнала нет.

Просьба о помощи идёт в реальный chat (+ ответ тьютора → полный диалог в чат-логе).
"""
import asyncio

from simulation.help_text import HelpTextGen
from simulation.policy import Action
from simulation.profiles import StudentProfile

_CONSOLE_ACTIONS = (Action.CORRECT_CMD, Action.WRONG_CMD, Action.REPEAT_ERROR)


class GNS3Actor:
    def __init__(
        self, node_tasks, consoles: dict, db_factory, backend_session_id: str,
        help_gen: HelpTextGen, profile: StudentProfile, save_user_message,
        save_assistant_message=None, tutor_reply=None, console_timeout: float = 5.0,
    ) -> None:
        self._tasks = list(node_tasks)          # NodeTask: node, correct_cmd, wrong_cmd
        self._consoles = consoles               # node name → (host, port)
        self._db_factory = db_factory
        self._backend_session_id = backend_session_id
        self._help_gen = help_gen
        self._profile = profile
        self._save_user_message = save_user_message
        self._save_assistant_message = save_assistant_message  # ответ тьютора → чат-лог
        self._tutor_reply = tutor_reply
        self._console_timeout = console_timeout
        self._i = 0  # текущий узел: CORRECT продвигает, WRONG/REPEAT бьют в него же
        self._ask_count = 0  # номер просьбы о помощи — фразы не повторяются дословно
        # Что и где студент ввёл последним — узел и команда идут в диалог ПАРОЙ,
        # иначе тьютор цитирует команду от одного узла, а говорит про другой.
        self._last_cmd: str | None = None
        self._last_node: str | None = None

    async def execute(
        self, action: Action, cmd: str = "", help_context: dict | None = None
    ) -> None:
        if action in _CONSOLE_ACTIONS:
            await self._configure(action)
        elif action == Action.ASK_HELP:
            context = self._help_context(help_context)
            self._ask_count += 1
            text = await self._help_gen.generate(self._profile, context)
            msgs = [{"role": "user", "parts": [{"type": "text", "text": text}]}]
            async with self._db_factory() as db:
                await self._save_user_message(db, self._backend_session_id, msgs)
            # Ответ тьютора → полный диалог в чат-логе (LLM если доступен, иначе шаблон).
            if self._tutor_reply is not None and self._save_assistant_message is not None:
                reply = await self._tutor_reply(text, context)
                async with self._db_factory() as db:
                    await self._save_assistant_message(
                        db, self._backend_session_id,
                        [{"type": "text", "text": reply}], None,
                    )
        elif action == Action.IDLE:
            await asyncio.sleep(self._idle_seconds())
        # SUBMIT: завершение обрабатывает оркестратор

    def _help_context(self, base: dict | None) -> dict:
        """Контекст диалога: узел, что студент ввёл, какая это по счёту просьба.

        Без него шаблоны вырождались в одну фразу, и чат-лог зацикливался.
        """
        context = dict(base or {})
        context.setdefault("attempt", self._ask_count)
        # Узел берём тот, на котором студент только что работал (а не «следующий»),
        # чтобы процитированная команда и узел в диалоге относились к одному и тому же.
        node = self._last_node
        if node is None and self._tasks:
            node = self._tasks[self._i % len(self._tasks)].node
        if node:
            context.setdefault("node", node)
        if self._last_cmd:
            context.setdefault("tried", self._last_cmd)
        return context

    async def _configure(self, action: Action) -> None:
        """Пишет конфиг в консоль узла. REPEAT_ERROR — та же неверная команда снова
        (проверка падает с тем же actual → `check_failing` → error_repeat_count)."""
        if not self._tasks:
            return
        task = self._tasks[self._i % len(self._tasks)]
        if action == Action.CORRECT_CMD:
            cmd = task.correct_cmd
            self._i += 1  # настроил узел — переходит к следующему
        else:
            cmd = task.wrong_cmd
        self._last_cmd, self._last_node = cmd, task.node  # контекст диалога с тьютором
        await self._send_console(task.node, cmd)

    async def _send_console(self, node: str, cmd: str) -> None:
        endpoint = self._consoles.get(node)
        if not endpoint:
            return
        host, port = endpoint
        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(host, port), timeout=self._console_timeout
            )
        except Exception:
            return  # консоль недоступна — прогон не роняем
        try:
            writer.write((cmd + "\r\n").encode())
            await writer.drain()
        except Exception:
            pass
        finally:
            writer.close()
            try:
                await writer.wait_closed()
            except Exception:
                pass

    def _idle_seconds(self) -> float:
        """Пауза простоя: медленнее у низкого темпа."""
        return 0.1 + (1.0 - self._profile.pace)
