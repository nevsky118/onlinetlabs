"""Реестр агентов для маршрутизации без поздних импортов.

Каждая запись хранит класс агента и тип входной модели. Конструкторы у агентов
отличаются (mcp_client, db), поэтому фабрикой агента занимается оркестратор.
"""

from agents.hint.agent import HintAgent
from agents.hint.models import HintInput
from agents.tutor.agent import TutorAgent
from agents.tutor.models import TutorInput

AGENT_REGISTRY: dict[str, tuple[type, type]] = {
    "tutor": (TutorAgent, TutorInput),
    "hint": (HintAgent, HintInput),
}
