"""Реестр агентов для маршрутизации без поздних импортов.

Каждая запись хранит класс агента и тип входной модели. Конструкторы у агентов
отличаются (mcp_client, db), поэтому фабрикой агента занимается оркестратор.
"""

from agents.analytics.agent import AnalyticsAgent
from agents.analytics.models import AnalyticsInput
from agents.hint.agent import HintAgent
from agents.hint.models import HintInput
from agents.lab.agent import LabAgent
from agents.lab.models import LabQueryInput
from agents.tutor.agent import TutorAgent
from agents.tutor.models import TutorInput
from agents.validator.agent import ValidatorAgent
from agents.validator.models import ValidationInput

AGENT_REGISTRY: dict[str, tuple[type, type]] = {
    "tutor": (TutorAgent, TutorInput),
    "lab": (LabAgent, LabQueryInput),
    "validator": (ValidatorAgent, ValidationInput),
    "analytics": (AnalyticsAgent, AnalyticsInput),
    "hint": (HintAgent, HintInput),
}
