"""Sim-student's help-request text: LLM (gated) + budget guard + templates.

The only place LLM is used in the simulation. When the flag is off / budget is
exhausted / on error — falls back to a template.

The template must depend on CONTEXT and ATTEMPT NUMBER: previously it was chosen
only by profile traits, so one student sent the exact same phrase all session,
and the chat log turned into a looping feed. A real student, once stuck, rephrases
and adds detail.
"""
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field

from simulation.profiles import StudentProfile

# llm_call(prompt) -> (text, tokens_used)
LLMCall = Callable[[str], Awaitable[tuple[str, int]]]

# Escalating requests: a general question first, then detail and frustration.
_ASK_STAGES = [
    "Не пойму, что не так{where}. Подскажешь?",
    "Я ввёл `{tried}`{where}, но проверка всё равно не проходит. Что не так?",
    "Уже несколько раз пробовал{where} — результат тот же. Куда смотреть?",
    "Всё ещё не сходится{where}. Можешь показать, каким должен быть адрес?",
    "Кажется, я хожу по кругу{where}. Дай, пожалуйста, конкретную подсказку.",
]
_ASK_FALLBACK = "Не пойму, что не так{where}. Подскажешь?"


@dataclass
class HelpTextGen:
    llm_enabled: bool
    budget_rub: float
    price_per_1k_rub: float
    llm_call: LLMCall | None = None
    spent_rub: float = field(default=0.0)

    async def generate(self, profile: StudentProfile, context: dict) -> str:
        """Request text. LLM if enabled AND budget not exhausted, else template."""
        if (
            not self.llm_enabled
            or self.llm_call is None
            or self.spent_rub >= self.budget_rub
        ):
            return self._template(profile, context)
        try:
            text, tokens = await self.llm_call(self._prompt(profile, context))
            self.spent_rub += tokens / 1000.0 * self.price_per_1k_rub
            return text
        except Exception:
            return self._template(profile, context)

    def _template(self, profile: StudentProfile, context: dict) -> str:
        """Phrase depends on attempt and context → no identical messages back to back."""
        attempt = int(context.get("attempt", 0))
        node = context.get("node")
        tried = context.get("tried")

        # Shift by traits — different students start with different phrasings.
        offset = int(profile.help_propensity * 10 + profile.skill * 3)
        stage = _ASK_STAGES[(offset + attempt) % len(_ASK_STAGES)]
        if "{tried}" in stage and not tried:
            stage = _ASK_FALLBACK

        where = f" на {node}" if node else ""
        return stage.format(where=where, tried=tried or "")

    def _prompt(self, profile: StudentProfile, context: dict) -> str:
        node = context.get("node") or "узле"
        tried = context.get("tried")
        attempt = int(context.get("attempt", 0))
        tried_part = f" Я ввёл команду `{tried}`, но проверка не проходит." if tried else ""
        return (
            f"Ты студент (навык {profile.skill:.1f}), настраиваешь сеть в лабе на {node}. "
            f"Шаг: {context.get('step', '?')}.{tried_part} "
            f"Это твоя {attempt + 1}-я просьба о помощи — не повторяй прошлые формулировки. "
            "Напиши короткую просьбу тьютору, естественным языком, 1-2 предложения."
        )
