"""Agent registry for routing without late imports.

Each entry stores the agent class and its input model type. Agent constructors
differ (mcp_client, db), so the orchestrator handles agent construction.
"""

from agents.hint.agent import HintAgent
from agents.hint.models import HintInput
from agents.tutor.agent import TutorAgent
from agents.tutor.models import TutorInput

AGENT_REGISTRY: dict[str, tuple[type, type]] = {
    "tutor": (TutorAgent, TutorInput),
    "hint": (HintAgent, HintInput),
}
