"""GNS3 executor: turns a simulated student action into console input, chat or idle.

The detector is fed by spec-check failures: LabProgressObserver telnets into the
node console, runs the lab checks and emits check_failing / check_retry /
check_regressed as error events. Those produce error_repeat_count,
distinct_failing_actuals and cycles_failing_unchanged, i.e. 4 of the 6 rules.

So the actor must configure the device for real and the nodes must stay running:
a stopped node has no console, the checks hang and the detector gets no signal.
Help requests go through the real chat, so the dialogue is persisted too.
"""

import asyncio

from simulation.help_text import HelpTextGen
from simulation.policy import Action
from simulation.profiles import StudentProfile

_CONSOLE_ACTIONS = (Action.CORRECT_CMD, Action.WRONG_CMD, Action.REPEAT_ERROR)


class GNS3Actor:
    def __init__(
        self,
        node_tasks,
        consoles: dict,
        db_factory,
        backend_session_id: str,
        help_gen: HelpTextGen,
        profile: StudentProfile,
        save_user_message,
        save_assistant_message=None,
        tutor_reply=None,
        console_timeout: float = 5.0,
    ) -> None:
        self._tasks = list(node_tasks)  # NodeTask: node, correct_cmd, wrong_cmd
        self._consoles = consoles  # node name → (host, port)
        self._db_factory = db_factory
        self._backend_session_id = backend_session_id
        self._help_gen = help_gen
        self._profile = profile
        self._save_user_message = save_user_message
        self._save_assistant_message = save_assistant_message  # tutor's reply → chat log
        self._tutor_reply = tutor_reply
        self._console_timeout = console_timeout
        self._i = 0  # current node: CORRECT advances it, WRONG/REPEAT hit the same one
        self._ask_count = 0  # help-request number, so phrases don't repeat verbatim
        # What and where the student typed last, node and command travel together into
        # the dialogue, otherwise the tutor quotes a command from one node while talking about another.
        self._last_cmd: str | None = None
        self._last_node: str | None = None

    async def execute(self, action: Action, help_context: dict | None = None) -> None:
        if action in _CONSOLE_ACTIONS:
            await self._configure(action)
        elif action == Action.ASK_HELP:
            context = self._help_context(help_context)
            self._ask_count += 1
            text = await self._help_gen.generate(self._profile, context)
            msgs = [{"role": "user", "parts": [{"type": "text", "text": text}]}]
            async with self._db_factory() as db:
                await self._save_user_message(db, self._backend_session_id, msgs)
            # Tutor's reply → full dialogue in the chat log (LLM if available, else template).
            if self._tutor_reply is not None and self._save_assistant_message is not None:
                reply = await self._tutor_reply(text, context)
                async with self._db_factory() as db:
                    await self._save_assistant_message(
                        db,
                        self._backend_session_id,
                        [{"type": "text", "text": reply}],
                        None,
                    )
        elif action == Action.IDLE:
            await asyncio.sleep(self._idle_seconds())
        # SUBMIT: completion is handled by the orchestrator

    def _help_context(self, base: dict | None) -> dict:
        """Dialogue context: node, what the student typed, which request number this is.

        Without it templates degenerated into one phrase and the chat log looped.
        """
        context = dict(base or {})
        context.setdefault("attempt", self._ask_count)
        # Use the node the student just worked on (not the "next" one), so the
        # quoted command and the node in the dialogue refer to the same thing.
        node = self._last_node
        if node is None and self._tasks:
            node = self._tasks[self._i % len(self._tasks)].node
        if node:
            context.setdefault("node", node)
        if self._last_cmd:
            context.setdefault("tried", self._last_cmd)
        return context

    async def _configure(self, action: Action) -> None:
        """Writes config to the node's console. REPEAT_ERROR resends the same wrong command
        (check fails with the same actual → `check_failing` → error_repeat_count)."""
        if not self._tasks:
            return
        task = self._tasks[self._i % len(self._tasks)]
        if action == Action.CORRECT_CMD:
            cmd = task.correct_cmd
            self._i += 1  # node configured, move to the next one
        else:
            cmd = task.wrong_cmd
        self._last_cmd, self._last_node = cmd, task.node  # context for the tutor dialogue
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
            return  # console unreachable, don't fail the run
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
        """Idle pause: slower for lower pace."""
        return 0.1 + (1.0 - self._profile.pace)
